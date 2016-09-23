import sqlite3
import os
import shutil
import logging
from datetime import date, timedelta


# template used to format txt file
default_tpl = '''
********{title}********
[Date: {datetime}   Tags: {tags}]\n
{text}\n\n\n\n'''

sql_tag_with_count = '''
SELECT Tags.name, (SELECT COUNT(*) FROM Nikki_Tags
                   WHERE Nikki_Tags.tagid=Tags.id) AS count FROM Tags'''

sql_tag_names = 'SELECT name FROM tags WHERE id IN (SELECT tagid FROM nikki_tags WHERE nikkiid=?)'

sql_diary_formats = 'SELECT start,length,type FROM TextFormat WHERE nikkiid=?'

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


class DiaryBook:
    """This class handles save/read/import/export on SQLite3 database.

    Each table's function:
    Nikki: diary without format/tag fields.
    Nikki_Tags: mapping diary to tags
    Tags: tags
    TextFormat: rich text formats and their owner
    """
    ID, DATETIME, TEXT, TITLE, TAGS, FORMATS = range(6)
    instance = None

    def __init__(self, db_path=None):
        self._path = self._conn = None
        self._commit = self._exe = None  # shortcut, update after connect
        assert DiaryBook.instance is None
        DiaryBook.instance = self
        if db_path: self.connect(db_path)

    def __str__(self):
        return 'Diary Book (%s) with %s diaries' % (self._path, len(self))

    def __len__(self):
        return self._exe('SELECT COUNT(id) FROM Nikki').fetchone()[0]

    def __iter__(self):
        iter_all = self._exe('SELECT * FROM Nikki')
        return map(self._joined, iter_all)

    def __getitem__(self, key):
        r = self._exe('SELECT * FROM Nikki WHERE id=?', (key,)).fetchone()
        if r is None:
            raise IndexError
        return self._joined(r)

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
        cmd = 'SELECT * FROM Nikki ORDER BY ' + order + (' DESC' if reverse else '')
        for r in self._exe(cmd):
            yield self._joined(r)

    def _joined(self, r):
        tags = ' '.join(self._exe(sql_tag_names, (r[0],)).fetchone() or '')

        formats = self._exe(sql_diary_formats, (r[0],))
        # cursor object only generates once, so we make a list
        formats = list(formats) if formats else None

        return dict(id=r[0], title=r[3], datetime=r[1], text=r[2],
                    tags=tags, formats=formats)

    def exporttxt(self, path, selected=None):
        """Export to TXT file using template (python string formatting).
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
        """Get all tags from database. If getcount is True,
        return two-tuples (name, count) generator"""
        return tuple(self._exe(sql_tag_with_count if getcount else 'SELECT name FROM Tags'))

    def _gettagid(self, name):
        """Get tag-id by name"""
        return self._exe('SELECT id FROM Tags WHERE name=?', (name,)).fetchone()[0]

    def changetagname(self, oldname, name):
        self._exe('UPDATE Tags SET name=? WHERE name=?', (name, oldname))
        self._commit()

    def save(self, id, datetime, title, tags, text, formats, batch=False):
        """
        :param id: if id is -1, then add a new diary. Else update matched diary
        :param tags: None (skip saving tags) or a string contains space-separated tags
        :param batch: commit will be skipped if True
        :return: the id of saved diary if not batch, else None
        """
        new = id == -1

        if new:
            cur = self._exe('INSERT INTO Nikki VALUES(NULL,?,?,?)',
                            (datetime, text, title))
            id = cur.lastrowid
        else:
            self._exe('UPDATE Nikki SET datetime=?, text=?, title=? WHERE id=?',
                      (datetime, text, title, id))
        # formats processing
        if not new:  # delete existing format information
            self._exe('DELETE FROM TextFormat WHERE nikkiid=?', (id,))
        for i in (formats or []):
            self._exe('INSERT INTO TextFormat VALUES(?,?,?,?)', (id,) + i)
        # tags processing
        if tags is not None:
            if not new:  # delete existing tags first
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

    def getpath(self):
        return self._path

    def get_datetime_range(self):
        return self._exe('SELECT min(datetime), max(datetime) from Nikki').fetchone()


def list_backups():
    try:
        files = sorted(os.listdir('backup'))
    except FileNotFoundError:
        return []
    fil = lambda x: len(x)>10 and x[4]==x[7]=='-' and x[10]=='_'
    return list(filter(fil, files))


def restore_backup(bk_name):
    logging.info('restore backup: %s', bk_name)
    db = DiaryBook.instance
    db.disconnect()
    bk_path = os.path.join('backup', bk_name)
    shutil.copyfile(bk_path, db.getpath())
    db.connect(db.getpath())


def backup():
    """Do daily backup and delete old backups if not did yet."""
    db_path = DiaryBook.instance.getpath()
    if not os.path.isdir('backup'): os.mkdir('backup')
    backups = list_backups()
    newest = backups[-1] if backups else ''
    if newest.split('_')[0] == str(date.today()): return

    shutil.copyfile(db_path, os.path.join(
        'backup', str(date.today())+'_%d.db' % len(DiaryBook.instance)))
    logging.info('everyday backup succeeded')

    # delete old backups
    week_before = str(date.today() - timedelta(weeks=1))
    for i in backups:
        if not i < week_before: break
        os.remove(os.path.join('backup', i))
