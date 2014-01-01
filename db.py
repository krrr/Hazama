import sqlite3
import sys, os
import richtagparser
import logging
# id created modified plaintext text title

class Nikki:
    def __str__(self):
        c = self.conn.execute('SELECT COUNT(id) FROM Nikki').fetchone()[0]
        return '%s nikki in database' % c

    def __init__(self, dbpath):
        self.conn = sqlite3.connect(dbpath)

        self.conn.execute(('CREATE TABLE IF NOT EXISTS Tags'
                           '(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)'))
        self.conn.execute(('CREATE TABLE IF NOT EXISTS Nikki'
                           '(id INTEGER PRIMARY KEY, created TEXT NOT NULL,'
                           'modified TEXT NOT NULL, plaintext INTEGER,'
                           'text TEXT NOT NULL, title TEXT)'))
        self.conn.execute(('CREATE TABLE IF NOT EXISTS Nikki_Tags'
                           '(nikkiid INTEGER NOT NULL, tagid INTEGER NOT NULL,'
                           'PRIMARY KEY(nikkiid, tagid))'))
        self.conn.execute(('CREATE TABLE IF NOT EXISTS TextFormat'
                           '(nikkiid INTEGER, start INTEGER, '
                           'length INTEGER, type INTEGER)'))
        #self.conn.execute('CREATE INDEX IF NOT EXISTS createdIndex \
        #                   ON Nikki (created DESC)')

    def __getitem__(self, id):
        L = self.conn.execute('SELECT * FROM Nikki \
                              WHERE id=?', (id,)).fetchone()
        tags = self.conn.execute('SELECT tagid FROM Nikki_Tags WHERE \
                                 nikkiid = ?', (id,)).fetchall()
        if len(tagsL) >= 1:
            tags = ' '.join(tagsL) + ' '
        else:
            tags = ''
        
        return {'id': L[0], 'created': L[1], 'modified': L[2], \
                'plaintext': L[3], 'text': L[4], 'title': L[5], 'tags': tags}
                
    def impxml(self, xmlpath):
        "import CintaNotes XML file"
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(xmlpath)
        root = tree.getroot()

        startno = 1 if root.find('tags') else 0

        if startno == 1:
            for t in root[0]:   
                tag = (t.attrib['name'],)
                try:
                    self.conn.execute('INSERT INTO Tags VALUES(NULL,?)', tag)
                except:
                    pass
            self.commit()

        for i in range(startno, len(root)):
            plain = root[i].attrib.get('plainText', 0)
            if not plain: self.commit()  # for getting nikkiid in parseXMLrichtag
            text = root[i].text if root[i].text else ' '
            values = (self.transXMLdate(root[i].attrib['created']),
                      self.transXMLdate(root[i].attrib['modified']),
                      plain,
                      text if plain else self.parseXMLrichtag(text),
                      root[i].attrib['title'],)
            self.conn.execute('INSERT INTO Nikki VALUES(NULL,?,?,?,?,?)', values)
            
            if root[i].attrib['tags']:
                self.commit()  # for getting nikkiid
                nikkiid = self.conn.execute('SELECT max(id) FROM Nikki').fetchone()[0]
                for tag in root[i].attrib['tags'].split():
                    values = (nikkiid, self.conn.execute('SELECT id FROM Tags WHERE name=?',(tag,)).fetchone()[0])
                    self.conn.execute('INSERT INTO Nikki_Tags VALUES(?,?)',
                                      values)

        self.conn.commit()

    def transXMLdate(self, x):
        x = x.replace('T', '')
        x = x[:4] + '/' + x[4:6] + '/' + x[6:8] + ' ' + \
        x[8:10] + ':' + x[10:12]

        return x

    def sorted(self, orderby='created', reverse=True):
        comm = '''SELECT * FROM Nikki ORDER BY ''' + \
               orderby + (' DESC' if reverse else '')
        t = self.conn.execute(comm)
        for L in t:
            tags = self.conn.execute('SELECT tagid FROM Nikki_Tags WHERE \
                                     nikkiid = ?', (L[0],)).fetchall()

            tagsL = [self.gettag(i[0]) for i in tags]
            if len(tagsL) >= 1:
                tags = ' '.join(tagsL) + ' '
            else:
                tags = ''
            yield {'id': L[0], 'created': L[1], 'modified': L[2], \
                   'plaintext': L[3], 'text': L[4], 'title': L[5], \
                   'tags': tags}

    def delete(self, id):
        self.conn.execute('DELETE FROM Nikki WHERE id = ?', (id,))
        try:
            self.conn.execute('DELETE FROM Nikki_Tags WHERE \
                             nikkiid = ?', (id,))
        except:
            pass

    def commit(self):
        self.conn.commit()

    def gettag(self, tagid=None):
        if tagid:
            return self.conn.execute('SELECT name FROM Tags WHERE \
                                     id = ?', (tagid,)).fetchone()[0]
        else:  # get all tags
            result = self.conn.execute('SELECT name FROM Tags')
            return [n[0] for n in result]
            
    def parseXMLrichtag(self, text):
        nikkiid = self.getnewid()

        parser = richtagparser.RichTagParser(strict=False)
        parser.myfeed(nikkiid, text, self.conn)
        
        return parser.getstripped()

    def getformat(self, id):
        return self.conn.execute('SELECT start, length, type \
                                 FROM TextFormat WHERE nikkiid = ?', (id,))
        
    def save(self, id, created, modified, html, title, tags):
        new = not bool(id)  # new is True if current nikki is new one
        if new: id=self.getnewid()

        logging.info('Saving ID: %s' % id)

        parser = richtagparser.NTextParser(strict=False)
        parser.myfeed(id, html, self.conn)
        text = parser.getstripped()
        plain = parser.plain

        if new:
            values = (id, created, modified, plain, text, title)
            self.conn.execute('INSERT INTO Nikki VALUES(?,?,?,?,?,?)', 
                              values)
        else:
            values = (created, modified, text, title, plain, id)
            self.conn.execute(('UPDATE Nikki SET created=?, modified=?, '
                              'text=?, title=?, plaintext=? '
                              'WHERE id=?'), values)
        # tags processing
        if not new:
            self.conn.execute('DELETE FROM Nikki_Tags WHERE nikkiid=?', (id,))
        for t in tags:
            try:
                self.conn.execute('INSERT INTO Tags VALUES(NULL,?)', (t,))
                self.commit()
            except:
                pass
            values = (id, self.conn.execute('SELECT id FROM Tags WHERE name=?', (t,)).fetchone()[0])
            self.conn.execute('INSERT INTO Nikki_Tags VALUES(?,?)', values)
        
        self.commit()
        return id

    def getnewid(self):
        maxid = self.conn.execute('SELECT max(id) FROM Nikki').fetchone()[0]
        return (maxid+1 if maxid else 1)

if __name__ == '__main__':
    path = os.path.split(__file__)[0] + os.sep
    n = Nikki(path+'test.db')
    
    # n.impxml(path+'\\xmlsample\\1.xml')
