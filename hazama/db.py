import sqlite3
import os
import shutil
from datetime import date, timedelta
import logging


# template used to format txt file
default_tpl = '''
********{title}********
[Date: {datetime}   Tags: {tags}]\n
{text}\n\n\n\n'''

sql_tag_with_count = '''
SELECT Tags.name, (SELECT COUNT(*) FROM Nikki_Tags
                   WHERE Nikki_Tags.tagid=Tags.id) AS count FROM Tags'''

sql_nikki_formats = 'SELECT start,length,type FROM TextFormat WHERE nikkiid=?'

schema = '''
CREATE TABLE IF NOT EXISTS Tags
    (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS Nikki
    (id INTEGER PRIMARY KEY, datetime TEXT NOT NULL,
     text TEXT NOT NULL, title TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS Nikki_Tags
    (nikkiid INTEGER NOT NULL REFERENCES Nikki(id) ON DELETE CASCADE,
     tagid INTEGER NOT NULL, PRIMARY KEY(nikkiid, tagid));
CREATE TABLE IF NOT EXISTS TextFormat
    (nikkiid INTEGER NOT NULL REFERENCES Nikki(id) ON DELETE CASCADE,
     start INTEGER NOT NULL, length INTEGER NOT NULL, type INTEGER NOT NULL);
CREATE TRIGGER IF NOT EXISTS autodeltag AFTER DELETE ON Nikki_Tags
    BEGIN DELETE FROM Tags WHERE (SELECT COUNT(*) FROM Nikki_Tags WHERE
    Nikki_Tags.tagid=Tags.id)==0; END;
'''

DatabaseError = sqlite3.DatabaseError


class DatabaseLockedError(Exception): pass


class Nikki:
    """This class handles save/read/import/export on SQLite3 database.

    Each table's function:
    Nikki: diary without format/tag fields.
    Nikki_Tags: mapping diary to tags
    Tags: tags
    TextFormat: rich text formats and their owner
    """
    _instance = None

    def __init__(self, db_path=None):
        self._path = self._conn = None
        self._commit = self._exe = None  # shortcut, update after connect
        self.setinstance(self)
        if db_path: self.connect(db_path)

    def __str__(self):
        return 'Diary Book (%s) with %s diaries' % (self._path, len(self))

    def __len__(self):
        return self._exe('SELECT COUNT(id) FROM Nikki').fetchone()[0]

    def __iter__(self):
        iter_all = self._exe('SELECT * FROM Nikki')
        return map(self._makedict, iter_all)

    def __getitem__(self, key):
        r = self._exe('SELECT * FROM Nikki WHERE id=?', (key,)).fetchone()
        if r is None:
            raise IndexError
        return self._makedict(r)

    def connect(self, db_path):
        self._path = db_path
        if self._conn: self.disconnect()
        self._conn = sqlite3.connect(db_path, timeout=0)
        self._commit, self._exe = self._conn.commit, self._conn.execute

        self._exe('PRAGMA foreign_keys = ON')
        # prevent other instance from visiting one database
        self._exe('PRAGMA locking_mode = EXCLUSIVE')
        try:
            self._exe('BEGIN EXCLUSIVE')  # obtain lock by dummy transaction
        except sqlite3.OperationalError as e:
            if str(e).startswith('database is locked'):
                raise DatabaseLockedError
            else:
                raise
        self._check_schema()

    def disconnect(self):
        self._conn.close()
        self._conn = self._exe = None

    def _check_schema(self):
        self._conn.executescript(schema)

    def sorted(self, order, reverse=True):
        assert order in ['datetime', 'title', 'length']
        order = order.replace('length', 'LENGTH(text)')
        cmd = ('SELECT * FROM Nikki ORDER BY ' +
               order + (' DESC' if reverse else ''))
        for r in self._exe(cmd):
            yield self._makedict(r)

    def _makedict(self, r):
        """Make a dictionary that represents one diary"""
        tags_id = self._exe('SELECT tagid FROM Nikki_Tags WHERE '
                            'nikkiid=?', (r[0],))
        tags = ' '.join(self._exe('SELECT name FROM Tags WHERE id = ?',
                                  (i[0],)).fetchone()[0]
                        for i in tags_id) if tags_id else ''

        formats = self._exe(sql_nikki_formats, (r[0],))
        # cursor object only generates once, so we make a list
        formats = list(formats) if formats else None

        return dict(id=r[0], title=r[3], datetime=r[1], text=r[2],
                    tags=tags, formats=formats)

    def exporttxt(self, path, selected=None):
        """Export to TXT file using template(string format).
        If selected contains diary dictionaries, only export diaries in it."""
        file = open(path, 'w', encoding='utf-8')
        try:
            with open('template.txt', encoding='utf-8') as f:
                tpl = f.read()
            tpl_type = 'custom'
        except OSError:
            tpl = default_tpl
            tpl_type = 'default'
        for n in (self.sorted('datetime', False) if selected is None
                  else selected):
            file.write(tpl.format(**n))
        file.close()
        logging.info('exporting succeeded (template: %s)', tpl_type)

    def delete(self, id):
        self._exe('DELETE FROM Nikki WHERE id = ?', (id,))
        logging.info('diary deleted (ID: %s)' % id)
        self._commit()

    def gettags(self, getcount=False):
        """generate all tags from database. If getcount is True,
        return two-tuples (name, count) generator"""
        if getcount:  # get with counts, used in TagList
            return ((r[0], r[1]) for r in self._exe(sql_tag_with_count))
        else:
            return (n[0] for n in self._exe('SELECT name FROM Tags'))

    def _gettagid(self, name):
        """Get tag-id by name"""
        return self._exe('SELECT id FROM Tags WHERE name=?',
                         (name,)).fetchone()[0]

    def changetagname(self, oldname, name):
        self._exe('UPDATE Tags SET name=? WHERE name=?', (name, oldname))
        self._commit()

    def save(self, id, datetime, title, tags, text, formats, batch=False):
        """
        arguments:
        id - if id is -1, then add a new diary. Else update matched diary
        tags - string contains tags separated by space. if tags is None,
               skip saving tags.
        batch - commit will be skipped if True
        """
        new = id == -1
        id = self.getnewid() if new else id
        values = ((None, datetime, text, title) if new else
                  (datetime, text, title, id))
        cmd = ('INSERT INTO Nikki VALUES(?,?,?,?)' if new else
               'UPDATE Nikki SET datetime=?, text=?, title=? WHERE id=?')
        self._exe(cmd, values)
        # formats processing
        if not new:  # delete existed format information
            self._exe('DELETE FROM TextFormat WHERE nikkiid=?', (id,))
        if formats:
            for i in formats:
                cmd = 'INSERT INTO TextFormat VALUES(?,?,?,?)'
                self._exe(cmd, (id,) + i)
        # tags processing
        if tags is not None:
            if not new:  # if diary isn't new, delete its tags first
                self._exe('DELETE FROM Nikki_Tags WHERE nikkiid=?', (id,))
            for t in tags.split():
                try:
                    tag_id = self._gettagid(t)
                except TypeError:  # tag not exists
                    self._exe('INSERT INTO Tags VALUES(NULL,?)', (t,))
                    self._commit()
                    tag_id = self._gettagid(t)
                self._exe('INSERT INTO Nikki_Tags VALUES(?,?)', (id, tag_id))
        if not batch:
            self._commit()
            logging.info('diary saved(ID: %s)' % id)
            return id

    def getnewid(self):
        max_id = self._exe('SELECT max(id) FROM Nikki').fetchone()[0]
        return max_id + 1 if max_id else 1

    def getpath(self):
        return self._path

    @classmethod
    def setinstance(cls, instance):
        assert cls._instance is None
        cls._instance = instance

    @classmethod
    def getinstance(cls):
        return cls._instance


def list_backups():
    try:
        files = sorted(os.listdir('backup'))
    except FileNotFoundError:
        return []
    fil = lambda x: (len(x) > 10) and (x[4] == x[7] == '-') and (x[10] == '_')
    return list(filter(fil, files))


def restore_backup(bk_name):
    logging.info('restore backup: %s', bk_name)
    nikki = Nikki.getinstance()
    nikki.disconnect()
    bk_path = os.path.join('backup', bk_name)
    shutil.copyfile(bk_path, nikki.getpath())
    nikki.connect(nikki.getpath())


def backup():
    """Do daily backup and delete old backups if not did yet."""
    db_path = Nikki.getinstance().getpath()
    if not os.path.isdir('backup'): os.mkdir('backup')
    backups = list_backups()
    newest = backups[-1] if backups else ''
    if newest.split('_')[0] == str(date.today()): return

    shutil.copyfile(db_path, os.path.join(
        'backup', str(date.today())+'_%d.db' % len(Nikki.getinstance())))
    logging.info('everyday backup succeeded')

    # delete old backups
    week_before = str(date.today() - timedelta(weeks=1))
    for i in backups:
        if not i < week_before: break
        os.remove(os.path.join('backup', i))
