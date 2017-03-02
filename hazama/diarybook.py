import sqlite3
import os
import sys
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
    DiaryModel is just a copy/cache of this.

    Tables:
    Nikki: diary without format/tag fields.
    Nikki_Tags: mapping diary to tags
    Tags: tags' name
    TextFormat: rich text formats

    Columns meaning:
    ID: rowid from database, id of deleted row may be reused
    DATETIME:
    TEXT:
    TITLE:
    TAGS: space separated tags
    FORMATS: tuple of 3-tuples (start, len, type)
    """
    ID, DATETIME, TEXT, TITLE, TAGS, FORMATS = range(6)
    EMPTY_DIARY = (-1, '', '', '', '', None)
    instance = None

    def __init__(self, db_path=None):
        self.path = self._conn = None
        self._commit = self._exe = None  # shortcut, update after connect
        assert DiaryBook.instance is None
        DiaryBook.instance = self
        if db_path:
            self.connect(db_path)

    def __str__(self):
        return 'Diary Book (%s) with %s diaries' % (self.path, len(self))

    def __len__(self):
        return self._exe('SELECT COUNT(id) FROM Nikki').fetchone()[0]

    def __iter__(self):
        return map(self._joined, self._exe('SELECT * FROM Nikki'))

    def __getitem__(self, id_):
        r = self._exe('SELECT * FROM Nikki WHERE id=?', (id_,)).fetchone()
        if r is None:
            raise KeyError
        return self._joined(r)

    def connect(self, db_path):
        self.path = db_path
        if self._conn: self.disconnect()
        self._conn = sqlite3.connect(db_path, timeout=0)
        self._commit, self._exe = self._conn.commit, self._conn.execute

        self._exe('PRAGMA foreign_keys = ON')

        # prevent other instance from visiting one database
        self._exe('PRAGMA locking_mode = EXCLUSIVE')
        if sys.version_info[:3] != (3, 6, 0):  # this py version has bug in sqlite module
            try:
                self._exe('BEGIN EXCLUSIVE')  # obtain lock by dummy transaction
            except sqlite3.OperationalError as e:
                if str(e).startswith('database is locked'):
                    raise DatabaseLockedError
                else:
                    raise
        self._conn.executescript(schema)  # check schema

    def disconnect(self):
        self._conn.close()
        self._conn = self._exe = None

    def sorted(self, order, reverse=True):
        assert order in ['datetime', 'title', 'length']
        order = order.replace('length', 'LENGTH(text)')
        cmd = 'SELECT * FROM Nikki ORDER BY ' + order + (' DESC' if reverse else '')
        return map(self._joined, self._exe(cmd))

    def _joined(self, r):
        tags = ' '.join(i[0] for i in self._exe(sql_tag_names, (r[0],)))
        formats = tuple(self._exe(sql_diary_formats, (r[0],))) or None
        return r + (tags, formats)

    def export_txt(self, path, selected=None):
        """Export to TXT file using template (python string formatting).
        If selected contains diaries, then only export diaries in it."""
        file = open(path, 'w', encoding='utf-8')
        try:
            with open('template.txt', encoding='utf-8') as f:
                tpl = f.read()
            tpl_type = 'custom'
        except OSError:
            tpl = default_tpl
            tpl_type = 'default'
        for d in (selected or self.sorted('datetime', False)):
            file.write(tpl.format(**diary2dict(d)))
        file.close()
        logging.info('exporting succeeded (template: %s)', tpl_type)

    def delete(self, id_):
        self._exe('DELETE FROM Nikki WHERE id = ?', (id_,))
        logging.info('diary deleted (ID: %s)' % id_)
        # tag data will be deleted automatically by trigger
        self._commit()

    def get_tags(self, count=False):
        """Get all tags from database. If count is True then
        return two-tuples (name, count) generator."""
        return tuple(self._exe(sql_tag_with_count) if count else
                     (r[0] for r in self._exe('SELECT name FROM Tags')))

    def _get_tag_id(self, name):
        """Get tag-id by name, because TagList doesn't store id (lazy)."""
        return self._exe('SELECT id FROM Tags WHERE name=?', (name,)).fetchone()[0]

    def change_tag_name(self, old, new):
        self._exe('UPDATE Tags SET name=? WHERE name=?', (new, old))
        self._commit()

    def save(self, diary, batch=False):
        """Save diary. If tags is None then skip saving tags.
        :param diary: tuple or dict
        :param batch: commit will be skipped if True
        :return: the id of saved diary if batch is False, otherwise None
        """
        diary = diary2dict(diary)
        id_ = diary['id']
        new = id_ == -1

        if new:
            cur = self._exe('INSERT INTO Nikki VALUES(NULL, :datetime, '
                            ':text, :title)', diary)
            id_ = cur.lastrowid
        else:
            self._exe('UPDATE Nikki SET datetime=:datetime, text=:text, '
                      'title=:title WHERE id=:id', diary)
        # formats processing
        if not new:  # delete existing format information
            self._exe('DELETE FROM TextFormat WHERE nikkiid=?', (id_,))
        for i in (diary['formats'] or []):
            self._exe('INSERT INTO TextFormat VALUES(?,?,?,?)', (id_,) + i)
        # tags processing
        if diary['tags'] is not None:
            if not new:  # delete existing tags first
                self._exe('DELETE FROM Nikki_Tags WHERE nikkiid=?', (id_,))
            for t in diary['tags'].split():
                try:
                    tag_id = self._get_tag_id(t)
                except TypeError:  # tag not exists
                    self._exe('INSERT INTO Tags VALUES(NULL,?)', (t,))
                    tag_id = self._get_tag_id(t)
                self._exe('INSERT INTO Nikki_Tags VALUES(?,?)', (id_, tag_id))

        if not batch:
            self._commit()
            logging.info('diary saved (ID: %s)' % id_)
            return id_

    def get_datetime_range(self):
        return self._exe('SELECT min(datetime), max(datetime) from Nikki').fetchone()


def diary2dict(d):
    if isinstance(d, dict):
        return d
    return {'id': d[0], 'datetime': d[1], 'text': d[2], 'title': d[3],
            'tags': d[4], 'formats': d[5]}


def dict2diary(d, as_list=False):
    ret = (d['id'], d['datetime'], d['text'], d['title'], d['tags'], d['formats'])
    return list(ret) if as_list else ret


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
    shutil.copyfile(bk_path, db.path)
    db.connect(db.path)


def backup():
    """Do daily backup and delete old backups if not did yet."""
    db_path = DiaryBook.instance.path
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
