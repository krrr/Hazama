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
    """setXX methods are used in NTextDocument and NTextEdit to apply formats."""
    HlColor = QColor(248, 162, 109, 100)
    Bold, HighLight, Italic, StrikeOut, UnderLine = range(1, 6)

    def setHL(self, apply):
        """Apply HighLight format to current selection if true, otherwise
        clear that format"""
        fmt = self.textCursor().charFormat()
        if apply:
            fmt.setBackground(QBrush(self.HlColor))
            self.textCursor().mergeCharFormat(fmt)
        else:
            fmt.clearProperty(QTextFormat.BackgroundBrush)
            self.textCursor().setCharFormat(fmt)

    def setBD(self, apply):
        fmt = self.textCursor().charFormat()
        if apply:
            fmt.setFontWeight(QFont.Bold)
            self.textCursor().mergeCharFormat(fmt)
        else:
            fmt.clearProperty(QTextFormat.FontWeight)
            self.textCursor().setCharFormat(fmt)

    def setSO(self, apply):
        fmt = self.textCursor().charFormat()
        if apply:
            fmt.setFontStrikeOut(True)
            self.textCursor().mergeCharFormat(fmt)
        else:
            fmt.clearProperty(QTextFormat.FontStrikeOut)
            self.textCursor().setCharFormat(fmt)

    def setUL(self, apply):
        fmt = self.textCursor().charFormat()
        if apply:
            fmt.setFontUnderline(True)
            self.textCursor().mergeCharFormat(fmt)
        else:
            fmt.clearProperty(QTextFormat.TextUnderlineStyle)
            self.textCursor().setCharFormat(fmt)

    def setIta(self, apply):
        fmt = self.textCursor().charFormat()
        if apply:
            fmt.setFontItalic(True)
            self.textCursor().mergeCharFormat(fmt)
        else:
            fmt.clearProperty(QTextFormat.FontItalic)
            self.textCursor().setCharFormat(fmt)


class NTextDocument(QTextDocument, TextFormatter):
    """QTextDocument with format setting function. Formats are three-tuple
    (startIndex, length, type), the same form in database."""

    def setText(self, text, formats=None):
        type2method = {1: self.setBD, 2: self.setHL, 3: self.setIta,
                       4: self.setSO, 5: self.setUL}
        self.setPlainText(text)
        if formats:
            self._cur = QTextCursor(self)
            for start, length, _type in formats:
                self._cur.setPosition(start)
                self._cur.setPosition(start + length, mode=self._cur.KeepAnchor)
                type2method[_type](apply=True)
            del self._cur

        self.clearUndoRedoStacks()
        self.setModified(False)

    def textCursor(self):
        """Make methods of TextFormatter to get right cursor"""
        return self._cur

    def setHlColor(self, color):
        """Used to set alpha-removed highlight color in NTextEdit"""
        self.HlColor = color

    @staticmethod
    def getFormats(qTextDoc):
        qFmtToFmt = [
            (NTextDocument.Bold, QTextFormat.FontWeight),
            (NTextDocument.HighLight, QTextFormat.BackgroundBrush),
            (NTextDocument.Italic, QTextFormat.FontItalic),
            (NTextDocument.StrikeOut, QTextFormat.FontStrikeOut),
            (NTextDocument.UnderLine, QTextFormat.TextUnderlineStyle),
        ]

        out = []
        block = qTextDoc.begin()
        while block.isValid():
            fragIter = block.begin()
            for i in fragIter:
                frag = i.fragment()
                charFmt = frag.charFormat()
                fmts = [f for f, qF in qFmtToFmt if charFmt.hasProperty(qF)]
                for f in fmts:
                    out.append((frag.position(), frag.length(), f))
            block = block.next()
        return out

    def drawContentsColor(self, painter, rect, color):
        """Using given color to draw contents"""
        painter.save()
        ctx = QAbstractTextDocumentLayout.PaintContext()
        ctx.palette.setColor(QPalette.Text, color)
        if rect.isValid():
            painter.setClipRect(rect)
            ctx.clip = rect
        self.documentLayout().draw(painter, ctx)
        painter.restore()

    def drawContentsPalette(self, painter, rect, palette):
        """Using given palette to draw contents instead of app default"""
        painter.save()
        ctx = QAbstractTextDocumentLayout.PaintContext()
        ctx.palette = palette
        if rect.isValid():
            painter.setClipRect(rect)
            ctx.clip = rect
        self.documentLayout().draw(painter, ctx)
        painter.restore()


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
