import re
from html.parser import HTMLParser



class RichTagParser(HTMLParser):
    curttag = None
    typedic = {'b': 1, 'em': 2, 'i': 3, 'strike':4, 'u': 5}

    def myfeed(self, nikkiid, text, conn):
        self.conn, self.nikkiid = conn, nikkiid
        self.stripped = re.sub('<[^<]+?>', '', text)
        self.feed(text)

    def getstripped(self):
        return self.stripped

    def handle_starttag(self, tag, attrs):
        self.curttag = tag if tag in self.typedic else None

    def handle_data(self, data):
        if self.curttag:
            type = self.typedic[self.curttag]
            start = self.stripped.index(data)
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
        
    def myfeed(self, nikkiid, text, conn):
        self.conn, self.nikkiid = conn, nikkiid
        try:     # avoid repeating record
            self.conn.execute('DELETE FROM TextFormat WHERE nikkiid=?',
                              (nikkiid,))
        except:
            pass
        text = '<p style' + text.partition('<p style')[2]
        self.stripped = re.sub('<[^<]+?>', '', text)
        self.feed(text)

    def getstripped(self):
        return self.stripped
        
    def handle_starttag(self, tag, attrs):
        if tag == 'span':
            for t in self.typedic:
                if t in attrs[0][1]:
                    self.curttype = self.typedic[t]

    def handle_data(self, data):
        if self.curttype:
            type = self.curttype
            start = self.stripped.index(data)
            length = len(data)
            self.conn.execute(('INSERT INTO TextFormat VALUES'
                              '(?,?,?,?)'), (self.nikkiid, start, length, type))
            self.plain = False
        self.curttype = None

        
if __name__ == '__main__':
     
    text = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html4
0/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'SimSun'; font-size:13px; font-weight:4
00; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;
 -qt-block-indent:0; text-indent:0px;">TTTTTTTTEEEEEEEESSSSSSSSSTTTTTTTTTT.<span
 style=" font-weight:600;">BOLD.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-le
ft:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;
 -qt-block-indent:0; text-indent:0px;">TTTTTTTTEEEEEEEESSSSSSSSSTTTTTTTTTT.<span
 style=" background-color:#fffaa0;">Highlight.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-le
ft:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;
 -qt-block-indent:0; text-indent:0px;">TTTTTTTTEEEEEEEESSSSSSSSSTTTTTTTTTT.<span
 style=" text-decoration: line-through;">strike out.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-le
ft:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;
 -qt-block-indent:0; text-indent:0px;">TTTTTTTTEEEEEEEESSSSSSSSSTTTTTTTTTT.<span
 style=" text-decoration: underline;">under line.</span></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-le
ft:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;
 -qt-block-indent:0; text-indent:0px;">TTTTTTTTEEEEEEEESSSSSSSSSTTTTTTTTTT.<span
 style=" font-style:italic;">Italic</span>。</p></body></html>'''

    n = NTextParser(strict=False)
    text = '<p style' + text.partition('<p style')[2]
    stripped = re.sub('<[^<]+?>', '', text)
    print(stripped)
