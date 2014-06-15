from PySide.QtCore import *
from PySide.QtGui import *


class TagCompleter(QCompleter):
    def __init__(self, tagList, parent=None):
        super(TagCompleter, self).__init__(tagList, parent)
        self.tagList = tagList
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
        if path in self.tagList or path is None:
            return ' '
        else:
            return [path, ]


class TextFormatter:
    """setXX methods are used in NTextDocument and NTextEdit(called by
    context-menu or shortcuts and rely on whether action checked or not).
    If used in NTextDocument,parameter pre of setXX methods should be True.
    """
    HlColor = QColor(248, 162, 109, 100)
    checkFuncs = [lambda self, x: x.background().color() == self.HlColor,
                  lambda __, x: x.fontWeight() == QFont.Bold,
                  lambda __, x: x.fontStrikeOut(),
                  lambda __, x: x.fontUnderline(),
                  lambda __, x: x.fontItalic()]

    def checkFormats(self):
        """Check formats in current selection and check or uncheck actions"""
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
            if not any(results): break
        for i, c in enumerate(results):
            self.acts[i].setChecked(c)

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


class NTextDocument(QTextDocument, TextFormatter):
    """Read format info from database and apply it."""
    type2method = {1: 'setBD', 2: 'setHL', 3: 'setIta', 4: 'setSO', 5: 'setUL'}

    def setText(self, text, formats=None):
        self.setPlainText(text)
        if formats:
            self.cur = QTextCursor(self)
            for r in formats:
                self.cur.setPosition(r[0])
                self.cur.setPosition(r[0] + r[1], mode=self.cur.KeepAnchor)
                getattr(self, self.type2method[r[2]])(pre=True)
            del self.cur

    def textCursor(self):
        """Make methods of TextFormatter to get right cursor"""
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


class MultiSortFilterProxyModel(QSortFilterProxyModel):
    """Simple Multi-Column ProxyModel, only supports fixed string"""
    fixedString = ''
    keyColumns = [0]

    def filterAcceptsRow(self, sourceRow, sourceParent):
        model = self.sourceModel()
        for i in self.keyColumns:
            if self.fixedString in model.data(model.index(sourceRow, i)):
                return True
        return False

    def setFilterFixedString(self, s):
        self.fixedString = s
        super(MultiSortFilterProxyModel, self).setFilterFixedString(s)

    def setFilterKeyColumns(self, *cols):
        self.keyColumns = cols

