import sqlite3
import sys
import os
import shutil
import time
import logging


# template used to format txt file
default_tpl = '''***{0[title]}***
[Date: {0[datetime]}]

{0[text]}\n\n\n\n'''


class Nikki:
    """This class hold a SQLite3 database,handling save/read/import/export.

    Each Table's function:
    Nikki: All diary saved here.(every one has all data except format/tag info).
    Nikki_Tags: Connecting tags to diary.
    Tags: All tags' body saved here.
    TextFormat: Connecting format info to diary.Format info itself also saved here.
    """

    def __str__(self):
        return '%s diary in database' % self.count()

    def __init__(self, db_path):
        self.setinstance(self)
        self.connect(db_path)
        self.conn.execute('CREATE TABLE IF NOT EXISTS Tags'
                          '(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)')
        self.conn.execute('CREATE TABLE IF NOT EXISTS Nikki'
                          '(id INTEGER PRIMARY KEY, datetime TEXT NOT NULL, '
                          'text TEXT NOT NULL, title TEXT NOT NULL)')
        self.conn.execute('CREATE TABLE IF NOT EXISTS Nikki_Tags'
                          '(nikkiid INTEGER NOT NULL REFERENCES Nikki(id) '
                          'ON DELETE CASCADE, tagid INTEGER NOT NULL,'
                          'PRIMARY KEY(nikkiid, tagid))')
        self.conn.execute('CREATE TABLE IF NOT EXISTS TextFormat'
                          '(nikkiid INTEGER NOT NULL REFERENCES Nikki(id) '
                          'ON DELETE CASCADE, start INTEGER NOT NULL, '
                          'length INTEGER NOT NULL, type INTEGER NOT NULL)')
        self.conn.execute('CREATE TRIGGER IF NOT EXISTS autodeltag AFTER '
                          'DELETE ON Nikki_Tags BEGIN   DELETE FROM Tags '
                          'WHERE (SELECT COUNT(*) FROM Nikki_Tags WHERE '
                          'Nikki_Tags.tagid=Tags.id)==0;  END')
        logging.info(str(self))

    def __getitem__(self, id):
        L = self.exe('SELECT * FROM Nikki WHERE id = ?', (id,)).fetchone()
        if not L:
            raise IndexError('id is not in database')
        tags_id = self.exe('SELECT tagid FROM Nikki_Tags WHERE '
                           'nikkiid = ?', (L[0],))
        tags = [self.gettag(i[0]) for i in tags_id] if tags_id else None
        formats = self.exe('SELECT start,length,type FROM TextFormat '
                           'WHERE nikkiid=?', (L[0],))
        # cursor object only generates once, so we make a list
        formats = [i for i in formats] if formats else None
        return dict(id=L[0], datetime=L[1], text=L[3],
                    title=L[4], tags=tags, formats=formats)

    def connect(self, db_path):
        self.path = db_path
        self.conn = sqlite3.connect(db_path)
        self.exe = self.conn.execute
        self.exe('PRAGMA foreign_keys = ON')

    def close(self):
        self.conn.close()

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
        logging.info('Export(XML) succeed')

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
        logging.info('Export succeed(use %s template)', hint)

    def sorted(self, order, reverse=True, *, tagid=None, search=None):
        if tagid and not search:  # only fetch nikki whose tagid match
            where = ('WHERE id IN (SELECT nikkiid FROM Nikki_Tags WHERE '
                     'tagid=%i) ') % tagid
        elif search and not tagid:
            where = ('WHERE datetime LIKE "%%%s%%" OR text LIKE "%%%s%%" '
                     'OR title LIKE "%%%s%%"') % ((search,) * 3)
        elif search and tagid:
            where = ('WHERE (id IN (SELECT nikkiid FROM Nikki_Tags WHERE '
                     'tagid=%i)) AND (datetime LIKE "%%%s%%" OR '
                     'text LIKE "%%%s%%" OR title LIKE "%%%s%%")' %
                     (tagid, search, search, search))
        else:
            where = ''
        if order == 'length':
            order = 'LENGTH(text)'
        cmd = ('SELECT * FROM Nikki ' + where + 'ORDER BY ' +
               order + (' DESC' if reverse else ''))
        for L in self.exe(cmd):
            tags_id = self.exe('SELECT tagid FROM Nikki_Tags WHERE '
                               'nikkiid = ?', (L[0],))
            tags = [self.gettag(i[0]) for i in tags_id] if tags_id else None
            formats = self.exe('SELECT start,length,type FROM TextFormat '
                               'WHERE nikkiid=?', (L[0],))
            # cursor object only generates once, so we make a list
            formats = [i for i in formats] if formats else None
            yield dict(id=L[0], datetime=L[1], text=L[2],
                       title=L[3], tags=tags, formats=formats)

    def delete(self, id):
        self.conn.execute('DELETE FROM Nikki WHERE id = ?', (id,))
        logging.info('Nikki deleted (ID: %s)' % id)
        self.commit()

    def commit(self):
        self.conn.commit()

    def count(self):
        return self.conn.execute('SELECT COUNT(id) FROM Nikki').fetchone()[0]

    def gettag(self, tagid=None, *, getcount=False):
        if tagid:  # get tags by id
            return self.conn.execute('SELECT name FROM Tags WHERE '
                                     'id = ?', (tagid,)).fetchone()[0]
        else:  # get all tags
            if getcount:  # get with counts.used in TList
                result = self.conn.execute('SELECT Tags.id,Tags.name,(SELECT '
                                           'COUNT(*) FROM Nikki_Tags WHERE Nikki_Tags.tagid=Tags.id) '
                                           'FROM Tags ORDER BY Tags.name')

                return result
            else:  # get without counts.used in tag completer
                result = self.conn.execute('SELECT name FROM Tags')
                return [n[0] for n in result]

    def gettagid(self, name):
        """Get tag-id by name"""
        return self.exe('SELECT id FROM Tags WHERE name=?',
                        (name,)).fetchone()[0]

    def save(self, new, id, datetime, title, tags, text, formats, batch=False):
        """
        arguments:
        batch - commit will be skipped if True
        """
        id = self.getnewid() if new else id
        values = ((None, datetime, text, title) if new else
                  (datetime, text, title, id))
        cmd = ('INSERT INTO Nikki VALUES(?,?,?,?)' if new else
               'UPDATE Nikki SET datetime=?, text=?, title=? WHERE id=?')
        self.exe(cmd, values)
        # formats processing
        if formats:
            if not new:  # delete existed format information
                self.exe('DELETE FROM TextFormat WHERE nikkiid=?', (id,))
            for i in formats:
                cmd = 'INSERT INTO TextFormat VALUES(?,?,?,?)'
                self.exe(cmd, (id,) + i)
        # tags processing
        if tags is not None:  # tags is None when not new and not changed
            if not new:  # if diary isn't new,delete its tags first
                self.exe('DELETE FROM Nikki_Tags WHERE nikkiid=?', (id,))
            for t in tags:
                try:
                    tagid = self.gettagid(t)
                except TypeError:  # tag not exists
                    self.exe('INSERT INTO Tags VALUES(NULL,?)', (t,))
                    self.commit()
                    tagid = self.gettagid(t)
                self.exe('INSERT INTO Nikki_Tags VALUES(?,?)', (id, tagid))
        if not batch:
            self.commit()
            logging.info('Nikki saved(ID: %s)' % id)
            return id

    def getnewid(self):
        maxid = self.conn.execute('SELECT max(id) FROM Nikki').fetchone()[0]
        return maxid + 1 if maxid else 1

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
        logging.info('Everyday backup succeed')
        # delete old backups
        weekbefore = time.strftime(fmt, time.localtime(int(time.time())-604800))
        for dname in backups:
            if dname < weekbefore:
                os.remove(os.path.join('backup', dname))
            else:
                break

