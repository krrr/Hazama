import re
from html.parser import HTMLParser

strip = re.compile(r'<[^<]+?>')

class RichTagParser(HTMLParser):
    curttag = None
    typedic = {'b': 1, 'em': 2, 'i': 3, 'strike':4, 'u': 5}

    def myfeed(self, nikkiid, text, conn):
        self.conn, self.nikkiid = conn, nikkiid
        self.striped = re.sub('<[^<]+?>', '', text)
        self.feed(text)

    def getstriped(self):
        return self.striped

    def handle_starttag(self, tag, attrs):
        self.curttag = tag if tag in self.typedic else None

    def handle_data(self, data):
        if self.curttag:
            type = self.typedic[self.curttag]
            start = self.striped.index(data)
            length = len(data)

            self.conn.execute(('INSERT INTO TextFormat VALUES'
                              '(?,?,?,?)'), (self.nikkiid, start, length, type))

        self.curttag = None


class NTextParser(HTMLParser):
    "Parse the output HTML of QTextDocument(NText)"
    plain = True
    curttype = None
    typedic = {'font-weight:600': 1, 'background-color:#fffaa0' : 2,
               'font-style:italic': 3, 'text-decoration: line-through': 4,
               'text-decoration: underline': 5}
    
    
    def myfeed(self, nikkiid, html, conn):
        self.conn, self.nikkiid = conn, nikkiid
        try:     # avoid repeating record
            self.conn.execute('DELETE FROM TextFormat WHERE nikkiid=?',
                              (nikkiid,))
        except Exception:
            pass
        self.html = ''.join(html.partition('<p style')[1:])
        self.striped = strip.sub('', self.html)
        self.feed(self.html)

    def getstriped(self):
        return self.striped
        
    def handle_starttag(self, tag, attrs):
        if tag == 'span':
            self.curttype = [self.typedic[t] for t in self.typedic 
                             if t in attrs[0][1]]
    def handle_data(self, data):
        if self.curttype:
            posInHtml = self.getindex()
            start = posInHtml - \
                    len(''.join(strip.findall(self.html[:posInHtml+1])))
            
            for type in self.curttype:
                self.conn.execute('INSERT INTO TextFormat VALUES(?,?,?,?)',
                                  (self.nikkiid, start, len(data), type))
            self.plain = False
        self.curttype = None

    def getindex(self):
        "transform line number and offset into index"
        line, offset = self.getpos()
        linesbefore = len(''.join(self.html.split('\n')[:line-1]))
        lfs = line-1
        
        return linesbefore + lfs + offset
        
        
        
if __name__ == '__main__':
     
    text = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'SimSun'; font-size:13px; font-weight:4
00; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;
 -qt-block-indent:0; text-indent:0px;"><span style=" text-decoration: line-throu
gh; background-color:#fffaa0;">TEST</span><span style=" background-color:#fffaa0
;">,TEST,TEST.</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;
 -qt-block-indent:0; text-indent:0px;"><span style=" text-decoration: underline;">TEST</span>.</p></body></html>'''
    html = ''.join(text.partition('<p style')[1:])
    
    n = NTextParser(strict=False)
    n.html = html
    n.striped = strip.sub('', html)
    n.feed(html)
