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

    # why these methods has silly parameter pre? it is used by NTextEdit
    # (format context menu and format shortcut), and deleting this parm will
    # add a pile of methods to NTextEdit.
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
    """QTextDocument with format setting function. Formats are tree-tuple
    (startIndex, length, type), the same form in database."""

    def setText(self, text, formats=None):
        type2method = {1: self.setBD, 2: self.setHL, 3: self.setIta,
                       4: self.setSO, 5: self.setUL}
        self.setPlainText(text)
        if formats:
            self.cur = QTextCursor(self)
            for start, length, _type in formats:
                self.cur.setPosition(start)
                self.cur.setPosition(start + length, mode=self.cur.KeepAnchor)
                type2method[_type](pre=True)
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
    """Multi-filter ProxyModel, every filter may associated with multiple columns,
    if any of columns match then it will pass that filter."""
    class Filter:
        cols = regExp = None

    def __init__(self, *args, **kwargs):
        super(MultiSortFilterProxyModel, self).__init__(*args, **kwargs)
        self._filters = []

    def filterAcceptsRow(self, sourceRow, sourceParent):
        model = self.sourceModel()

        def checkOneFilter(f):
            for c in f.cols:
                if f.regExp.indexIn(model.data(model.index(sourceRow, c))) != -1:
                    return True
            return False

        for f in self._filters:
            if not checkOneFilter(f):
                return False
        return True

    def setFilterPattern(self, id, pattern):
        """Set the filter's pattern specified by filter id"""
        self._filters[id].regExp.setPattern(pattern)
        # let filter model update
        super(MultiSortFilterProxyModel, self).setFilterFixedString('')

    def filterPattern(self, id):
        """Return the filter's pattern specified by filter id"""
        return self._filters[id].regExp.pattern()

    def addFilter(self, cols, patternSyntax=QRegExp.FixedString, cs=None):
        """Add new filter into proxy model.
        :param cols: a list contains columns to be filtered
        :param cs: Qt::CaseSensitivity, if None then use model's setting
        :return: the id of new filter, id starts from zero"""
        assert patternSyntax in [QRegExp.FixedString, QRegExp.Wildcard,
                                 QRegExp.WildcardUnix, QRegExp.RegExp], 'wrong pattern syntax'
        f = MultiSortFilterProxyModel.Filter()
        f.cols = tuple(cols)
        f.regExp = QRegExp('', self.filterCaseSensitivity() if cs is None else cs,
                           patternSyntax)
        self._filters.append(f)
        return len(self._filters) - 1

    def removeFilter(self, id):
        """Remove the filter specified by its id"""
        del self._filters[id]
