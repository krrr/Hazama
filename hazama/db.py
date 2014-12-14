import sqlite3
from sqlite3 import DatabaseError
import sys
import os
import shutil
import time
import logging


# template used to format txt file
default_tpl = '''***{0[title]}***
[Date: {0[datetime]}]

{0[text]}\n\n\n\n'''

sql_tag_with_count = '''
SELECT Tags.name, (SELECT COUNT(*) FROM Nikki_Tags
                   WHERE Nikki_Tags.tagid=Tags.id) AS count
FROM Tags'''

sql_nikki_formats = 'SELECT start,length,type FROM TextFormat WHERE nikkiid=?'


class Nikki:
    """This class hold a SQLite3 database,handling save/read/import/export.

    Each Table's function:
    Nikki: All diary saved here.(every one has all data except format/tag info).
    Nikki_Tags: Connecting tags to diary.
    Tags: All tags' body saved here.
    TextFormat: Connecting format info to diary.Format info itself also saved here.
    """
    path = conn = None
    exe = commit = close = None  # for convenience, updated after connection

    def __str__(self):
        return '%s diary in database' % self.count()

    def __init__(self, db_path):
        self.setinstance(self)
        self.connect(db_path)
        # reconnect by calling connect method will skip schema checking
        self.exe('CREATE TABLE IF NOT EXISTS Tags'
                 '(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)')
        self.exe('CREATE TABLE IF NOT EXISTS Nikki'
                 '(id INTEGER PRIMARY KEY, datetime TEXT NOT NULL, '
                 'text TEXT NOT NULL, title TEXT NOT NULL)')
        self.exe('CREATE TABLE IF NOT EXISTS Nikki_Tags'
                 '(nikkiid INTEGER NOT NULL REFERENCES Nikki(id) '
                 'ON DELETE CASCADE, tagid INTEGER NOT NULL,'
                 'PRIMARY KEY(nikkiid, tagid))')
        self.exe('CREATE TABLE IF NOT EXISTS TextFormat'
                 '(nikkiid INTEGER NOT NULL REFERENCES Nikki(id) '
                 'ON DELETE CASCADE, start INTEGER NOT NULL, '
                 'length INTEGER NOT NULL, type INTEGER NOT NULL)')
        self.exe('CREATE TRIGGER IF NOT EXISTS autodeltag AFTER '
                 'DELETE ON Nikki_Tags BEGIN   DELETE FROM Tags '
                 'WHERE (SELECT COUNT(*) FROM Nikki_Tags WHERE '
                 'Nikki_Tags.tagid=Tags.id)==0;  END')
        logging.info(str(self))

    def __iter__(self):
        self._iter_all = self.exe('SELECT * FROM Nikki')
        return self

    def __next__(self):
        r = self._iter_all.fetchone()
        if r is None:
            del self._iter_all
            raise StopIteration
        return self._makedict(r)

    def __getitem__(self, key):
        r = self.exe('SELECT * FROM Nikki WHERE id=?', (key,)).fetchone()
        return self._makedict(r)

    def connect(self, db_path):
        self.path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.commit, self.exe, self.close = (
            self.conn.commit, self.conn.execute, self.conn.close)

    def sorted(self, order, reverse=True):
        assert order in ['datetime', 'title', 'length']
        order = order.replace('length', 'LENGTH(text)')
        cmd = ('SELECT * FROM Nikki ORDER BY ' +
               order + (' DESC' if reverse else ''))
        for r in self.exe(cmd):
            yield self._makedict(r)

    def _makedict(self, r):
        """Make a dictionary that represents one diary"""
        tags_id = self.exe('SELECT tagid FROM Nikki_Tags WHERE '
                           'nikkiid=?', (r[0],))
        tags = ' '.join(self.exe('SELECT name FROM Tags WHERE id = ?',
                                 (i[0],)).fetchone()[0]
                        for i in tags_id) if tags_id else ''

        formats = self.exe(sql_nikki_formats, (r[0],))
        # cursor object only generates once, so we make a list
        formats = list(formats) if formats else None

        return dict(id=r[0], title=r[3], datetime=r[1], text=r[2],
                    tags=tags, formats=formats)

    def importxml(self, path):
        """Import XML file"""
        import xml.etree.ElementTree as ET
        tree = ET.parse(path)
        root = tree.getroot()
        for i in root:
            formats = i.find('formats')
            formats = [(f.get('start'), f.get('length'), f.get('type'))
                       for f in formats] if formats else None
            self.save(new=True, id=None, datetime=i.get('datetime'),
                      title=i.get('title'), tags=i.get('tags').split(),
                      text=i.text, formats=formats, batch=True)
        self.commit()

    def exportxml(self, path):
        """Export to XML file"""
        import xml.etree.ElementTree as ET
        root = ET.Element('nikkichou')
        for row in self.sorted('datetime'):
            nikki = ET.SubElement(root, 'nikki')
            for attr in ['title', 'datetime']:
                nikki.set(attr, row[attr])
            nikki.set('tags', ' '.join(row['tags']) if row['tags'] else '')
            nikki.text = row['text']
            # save format if current nikki has
            if row['formats']:
                formats = ET.SubElement(nikki, 'formats')
                for f in row['formats']:
                    fmt = ET.SubElement(formats, 'format')
                    for index, item in enumerate(['start', 'length', 'type']):
                        fmt.set(item, str(f[index]))
        tree = ET.ElementTree(root)
        tree.write(path, encoding='utf-8')
        logging.info('Exporting(XML) successful')

    def exporttxt(self, path, selected=None):
        """Export to TXT file using template(string format).
        When selected is a list contains nikki data,only export diary in list."""
        file = open(path, 'w', encoding='utf-8')
        try:
            with open('template.txt', encoding='utf-8') as f:
                tpl = f.read()
            hint = 'custom'
        except OSError:
            tpl = default_tpl
            hint = 'default'
        for n in (self.sorted('datetime', False) if selected is None
                  else selected):
            file.write(tpl.format(n))
        file.close()
        logging.info('Exporting successful(use %s template)', hint)

    def delete(self, id):
        self.exe('DELETE FROM Nikki WHERE id = ?', (id,))
        logging.info('Nikki deleted (ID: %s)' % id)
        self.commit()

    def count(self):
        return self.exe('SELECT COUNT(id) FROM Nikki').fetchone()[0]

    def gettags(self, getcount=False):
        """Get all tags from database,return a generator.If getcount is True,
        return two-tuples (name, count) generator"""
        if getcount:  # get with counts, used in TagList
            return ((r[0], r[1]) for r in self.exe(sql_tag_with_count))
        else:
            return (n[0] for n in self.exe('SELECT name FROM Tags'))

    def _gettagid(self, name):
        """Get tag-id by name"""
        return self.exe('SELECT id FROM Tags WHERE name=?',
                        (name,)).fetchone()[0]

    def changetagname(self, oldname, name):
        """Change tag's name only,leave associated diaries unchanged"""
        self.exe('UPDATE Tags SET name=? WHERE name=?', (name, oldname))
        self.commit()

    def save(self, new, id, datetime, title, tags, text, formats, batch=False):
        """
        arguments:
        tags - string contains tags separated by space. if tags is None,
               skip saving tags.
        batch - commit will be skipped if True
        """
        id = self.getnewid() if new else id
        values = ((None, datetime, text, title) if new else
                  (datetime, text, title, id))
        cmd = ('INSERT INTO Nikki VALUES(?,?,?,?)' if new else
               'UPDATE Nikki SET datetime=?, text=?, title=? WHERE id=?')
        self.exe(cmd, values)
        # formats processing
        if not new:  # delete existed format information
            self.exe('DELETE FROM TextFormat WHERE nikkiid=?', (id,))
        if formats:
            for i in formats:
                cmd = 'INSERT INTO TextFormat VALUES(?,?,?,?)'
                self.exe(cmd, (id,) + i)
        # tags processing
        if tags is not None:
            if not new:  # if diary isn't new, delete its tags first
                self.exe('DELETE FROM Nikki_Tags WHERE nikkiid=?', (id,))
            for t in tags.split():
                try:
                    tag_id = self._gettagid(t)
                except TypeError:  # tag not exists
                    self.exe('INSERT INTO Tags VALUES(NULL,?)', (t,))
                    self.commit()
                    tag_id = self._gettagid(t)
                self.exe('INSERT INTO Nikki_Tags VALUES(?,?)', (id, tag_id))
        if not batch:
            self.commit()
            logging.info('Nikki saved(ID: %s)' % id)
            return id

    def getnewid(self):
        max_id = self.exe('SELECT max(id) FROM Nikki').fetchone()[0]
        return max_id + 1 if max_id else 1

    def getpath(self):
        return self.path

    @classmethod
    def setinstance(cls, instance):
        cls.instance = instance

    @classmethod
    def getinstance(cls):
        return cls.instance


def list_backups():
    try:
        files = sorted(os.listdir('backup'))
    except FileNotFoundError:
        return []
    fil = lambda x: (len(x) > 10) and (x[4] == x[7] == '-') and (x[10] == '_')
    return [i for i in files if fil(i)]


def restore_backup(bk_name):
    logging.info('Restore backup: %s', bk_name)
    nikki = Nikki.getinstance()
    nikki.close()
    bk_path = os.path.join('backup', bk_name)
    shutil.copyfile(bk_path, nikki.getpath())
    nikki.connect(nikki.getpath())


def check_backup():
    """Check backups and do if necessary.Delete old backups."""
    db_path = Nikki.getinstance().getpath()
    if not os.path.isdir('backup'): os.mkdir('backup')
    backups = list_backups()
    fmt = '%Y-%m-%d'
    today = time.strftime(fmt)
    try:
        newest = backups[-1]
    except IndexError:  # empty directory
        newest = ''
    if newest.split('_')[0] != today:  # new day
        # make new backup
        nikki = Nikki.getinstance()
        shutil.copyfile(db_path, os.path.join('backup',
                                              today+'_%d.db' % nikki.count()))
        logging.info('Everyday backup successful')
        # delete old backups
        week_before = time.strftime(fmt, time.localtime(int(time.time())-604800))
        for i in backups:
            if i < week_before:
                os.remove(os.path.join('backup', i))
            else:
                break
