from PySide.QtCore import *
from PySide.QtGui import *
from config import settings


class TagCompleter(QCompleter):
    def __init__(self, tagL, parent=None):
        super(TagCompleter, self).__init__(tagL, parent)
        self.tagL = tagL
        self.setCaseSensitivity(Qt.CaseInsensitive)

    def pathFromIndex(self, index):
        # path is current matched tag.
        path = QCompleter.pathFromIndex(self, index)
        # a list like [tag1, tag2, tag3(maybe a part)]
        L = self.widget().text().split()
        if len(L) > 1:
            path = '%s %s ' % (' '.join(L[:-1]), path)
        else:
            path += ' '
        return path

    def splitPath(self, path):
        # path is tag string like "tag1 tag2 tag3(maybe a part) "
        path = path.split()[-1] if path.split() else None
        if path in self.tagL or path is None:
            return ' '
        else:
            return [path, ]


class TextFormatter:
    """setXX methods are used in NTextDocument and NTextEdit(called by
    context-menu or shortcuts, and always before checkFormat).
    If used in NTextDocument,parameter pre of setXX methods should be True.
    """
    HlColor = QColor(248, 162, 109, 100)
    checkFuncs = [lambda self, x: x.background().color() == self.HlColor,
                  lambda __, x: x.fontWeight() == QFont.Bold,
                  lambda __, x: x.fontStrikeOut(),
                  lambda __, x: x.fontUnderline(),
                  lambda __, x: x.fontItalic()]

    def checkFormat(self):
        """Check five formats in whole selection, return a result list in
        order of HighLight, Bold, StrikeOut, Underline, Italic"""
        cur = self.textCursor()
        start, end = cur.anchor(), cur.position()
        if start > end:
            start, end = end, start
        results = [True] * 5
        for pos in range(end, start, -1):
            cur.setPosition(pos)
            charFmt = cur.charFormat()
            for i, f in enumerate(self.checkFuncs):
                if results[i] and not f(self, charFmt):
                    results[i] = False
            if not any(results):
                return results
        return results

    def setHL(self, pre=False):
        fmt = QTextCharFormat()
        doFormat = True if pre else self.hlAct.isChecked()
        fmt.setBackground(QBrush(self.HlColor if doFormat else Qt.transparent))
        self.textCursor().mergeCharFormat(fmt)

    def setBD(self, pre=False):
        fmt = QTextCharFormat()
        doFormat = True if pre else self.bdAct.isChecked()
        fmt.setFontWeight(QFont.Bold if doFormat else QFont.Normal)
        self.textCursor().mergeCharFormat(fmt)

    def setSO(self, pre=False):
        fmt = QTextCharFormat()
        doFormat = True if pre else self.soAct.isChecked()
        fmt.setFontStrikeOut(doFormat)
        self.textCursor().mergeCharFormat(fmt)

    def setUL(self, pre=False):
        fmt = QTextCharFormat()
        doFormat = True if pre else self.ulAct.isChecked()
        fmt.setFontUnderline(doFormat)
        self.textCursor().mergeCharFormat(fmt)

    def setIta(self, pre=False):
        fmt = QTextCharFormat()
        doFormat = True if pre else self.itaAct.isChecked()
        fmt.setFontItalic(doFormat)
        self.textCursor().mergeCharFormat(fmt)


class SortOrderMenu(QMenu):
    """Menu used to Change sort order of NList."""
    def __init__(self, parent=None):
        super(SortOrderMenu, self).__init__(parent)
        self.aboutToShow.connect(self.setActs)
        # create actions
        self.bydatetime = QAction(self.tr('Date'), self)
        self.bytitle = QAction(self.tr('Title'), self)
        self.bylength = QAction(self.tr('Length'), self)
        self.reverse = QAction(self.tr('Reverse'), self)
        self.reverse.setCheckable(True)
        self.ordertypes = [self.bydatetime, self.bytitle, self.bylength]
        for a in self.ordertypes:
            a.setCheckable(True)
            self.addAction(a)
        self.addSeparator()
        self.addAction(self.reverse)

    def setActs(self):
        """Set actions checked/unchecked before showing"""
        order = settings['Main'].get('listorder', 'datetime')
        reverse = settings['Main'].getint('listreverse', 1)
        for a in self.ordertypes: a.setChecked(False)
        enabled = getattr(self, 'by' + order)
        enabled.setChecked(True)
        self.reverse.setChecked(reverse)


class NTextDocument(QTextDocument, TextFormatter):
    """Read format info from database and apply it."""
    typedic = {1: 'setBD', 2: 'setHL', 3: 'setIta', 4: 'setSO', 5: 'setUL'}

    def setText(self, text, formats=None):
        self.setPlainText(text)
        if formats:
            self.cur = QTextCursor(self)
            for r in formats:
                self.cur.setPosition(r[0])
                self.cur.setPosition(r[0] + r[1], mode=self.cur.KeepAnchor)
                getattr(self, self.typedic[r[2]])(pre=True)
            del self.cur

    def textCursor(self):
        """Make TextFormatter's methods to get right cursor"""
        return self.cur

    def setHlColor(self, color):
        """Used to set alpha-removed highlight color in NTextEdit"""
        self.HlColor = color


class NSplitter(QSplitter):
    """Fix default "Split Horizontal" old cursor on split handle"""
    def createHandle(self):
        handle = QSplitterHandle(Qt.Horizontal, self)
        handle.setCursor(Qt.SizeHorCursor)
        return handle

