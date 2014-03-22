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


class QtHtmlParser(HTMLParser):
    "Parse HTML of QTextDocument,return formats information"
    typedic = {'font-weight:600': 1, 'background-color:#fffaa0' : 2,
               'font-style:italic': 3, 'text-decoration: line-through': 4,
               'text-decoration: underline': 5}
    
    def myfeed(self, html):
        self.curttype = None
        self.formats = []
        self.pos_plain = 0
        self.html = html.split('</head>')[1]
        self.feed(self.html)
        return self.formats

    def handle_starttag(self, tag, attrs):
        if tag == 'span':
            self.curttype = [self.typedic[t] for t in self.typedic 
                             if t in attrs[0][1]]

    def handle_data(self, data):
        length = len(data)
        if self.curttype:
            for type in self.curttype:
                # (start, length, type)
                self.formats.append((self.pos_plain-1, length, type))
            self.curttype = None
        self.pos_plain += length

    def handle_entityref(self, name):
        # handle_data will ignore &,<,>
        self.pos_plain += 1

