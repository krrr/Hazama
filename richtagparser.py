import re
from html.parser import HTMLParser

strip = re.compile(r'<[^<]+?>')


class RichTagParser(HTMLParser):
    typedic = {'b': 1, 'em': 2, 'i': 3, 'strike': 4, 'u': 5}

    def __init__(self):
        HTMLParser.__init__(self)
        self.pos_plain = 0
        self.start = self.curt_type = self.stripped = None
        self.formats = []

    def feed(self, html):
        self.stripped = strip.sub('', html)
        HTMLParser.feed(self, html)
        return self.formats

    def getstripped(self):
        return self.stripped

    def handle_starttag(self, tag, attrs):
        self.start = self.pos_plain

    def handle_endtag(self, tag):
        # (start, length, type)
        self.formats.append((self.start, self.pos_plain-self.start,
                             self.typedic[tag]))

    def handle_data(self, data):
        self.pos_plain += len(data)


class QtHtmlParser(HTMLParser):
    """Parse HTML of QTextDocument,return formats information"""
    typedic = {'font-weight:600': 1, 'background-color:': 2,
               'font-style:italic': 3, 'text-decoration: line-through': 4,
               'text-decoration: underline': 5}

    def __init__(self):
        HTMLParser.__init__(self)
        self.curt_types = self.html = None
        self.pos_plain = -1  # first char is \n
        self.formats = []

    def feed(self, html):
        self.html = html.split('</head>')[1]
        HTMLParser.feed(self, self.html)
        return self.formats

    def handle_starttag(self, tag, attrs):
        if tag == 'span':
            self.curt_types = [self.typedic[t] for t in self.typedic
                               if t in attrs[0][1]]

    def handle_data(self, data):
        length = len(data)
        if self.curt_types:
            for _type in self.curt_types:
                # (start, length, type)
                self.formats.append((self.pos_plain, length, _type))
            self.curt_types = None
        self.pos_plain += length

    def handle_entityref(self, name):
        # handle_data will ignore &,<,>
        self.pos_plain += 1

