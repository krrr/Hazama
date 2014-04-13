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
    """All methods of this class are used in NTextDocument to set format.
    NTextEdit also use those to set format(called from context-menu).
    If used in NTextDocument,pre should be True.
    """
    hl_color = QColor(248, 162, 109, 100)

    def setHL(self, pre=False):
        fmt = self.textCursor().charFormat()
        if pre:  # called by NTextDocument
            hasFormat = False
        else:  # called by NTextEdit(Editor's context menu)
            hasFormat = (fmt.background().color() == self.hl_color)
        fmt.setBackground(QBrush(Qt.white if hasFormat else self.hl_color))
        self.textCursor().mergeCharFormat(fmt)

    def setBD(self, pre=False):
        fmt = self.textCursor().charFormat()
        if pre:
            hasFormat = False
        else:
            hasFormat = (fmt.fontWeight() == QFont.Bold)

        fmt.setFontWeight(QFont.Normal if hasFormat else QFont.Bold)
        self.textCursor().mergeCharFormat(fmt)

    def setSO(self, pre=False):
        fmt = self.textCursor().charFormat()
        if pre:
            hasFormat = False
        else:
            hasFormat = fmt.fontStrikeOut()

        fmt.setFontStrikeOut(not hasFormat)
        self.textCursor().mergeCharFormat(fmt)

    def setUL(self, pre=False):
        fmt = self.textCursor().charFormat()
        if pre:
            hasFormat = False
        else:
            hasFormat = fmt.fontUnderline()

        fmt.setFontUnderline(not hasFormat)
        self.textCursor().mergeCharFormat(fmt)

    def setIta(self, pre=False):
        fmt = self.textCursor().charFormat()
        if pre:
            hasFormat = False
        else:
            hasFormat = fmt.fontItalic()

        fmt.setFontItalic(not hasFormat)
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


class NSplitter(QSplitter):
    """Fix default "Split Horizontal" old cursor on split handle"""
    def createHandle(self):
        handle = QSplitterHandle(Qt.Horizontal, self)
        handle.setCursor(Qt.SizeHorCursor)
        return handle

