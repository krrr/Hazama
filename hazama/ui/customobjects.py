from PySide.QtCore import *
from PySide.QtGui import *


class TagCompleter(QCompleter):
    # QCompleter is not designed to use in this way, so these codes are terrible
    def __init__(self, tagList, parent=None):
        super().__init__(tagList, parent)
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


# noinspection PyUnresolvedReferences
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
    _type2method = [None, TextFormatter.setBD, TextFormatter.setHL, TextFormatter.setIta,
                    TextFormatter.setSO, TextFormatter.setUL]  # associated array

    def setText(self, text, formats=None):
        self.setPlainText(text)
        if formats:
            cur = self._cur = QTextCursor(self)
            for start, length, type_ in formats:
                cur.setPosition(start)
                cur.setPosition(start+length, cur.KeepAnchor)
                self._type2method[type_](self, True)
            del self._cur

        self.clearUndoRedoStacks()
        self.setModified(False)

    def textCursor(self):
        """Make methods of TextFormatter to get right cursor"""
        return self._cur

    def setHlColor(self, color):
        """Used to set alpha-removed highlight color in NTextEdit"""
        self.HlColor = color

    def getFormats(self):
        qFmtToFmt = [
            (NTextDocument.Bold, QTextFormat.FontWeight),
            (NTextDocument.HighLight, QTextFormat.BackgroundBrush),
            (NTextDocument.Italic, QTextFormat.FontItalic),
            (NTextDocument.StrikeOut, QTextFormat.FontStrikeOut),
            (NTextDocument.UnderLine, QTextFormat.TextUnderlineStyle),
        ]

        out = []
        block = self.begin()
        while block != self.end():
            for i in block.begin():
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
    """Multi-filter ProxyModel. Every filter may be associated with multiple columns,
    if any of columns match then it will pass that filter."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._filters = []  # list of 2-tuple (cols, QRegExp)

    def filterAcceptsRow(self, sourceRow, sourceParent):
        return all(self._checkOneFilter(self.sourceModel(), sourceRow, f)
                   for f in self._filters)

    def _checkOneFilter(self, model, sourceRow, f):
        if f is None:
            return True

        cols, regex = f
        return any(regex.indexIn(model.data(model.index(sourceRow, c))) != -1 for c in cols)

    def setFilterPattern(self, id_, pattern):
        """Set the filter's pattern specified by filter id"""
        self._filters[id_][1].setPattern(pattern)
        super().setFilterFixedString('')  # let filter model update

    def filterPattern(self, id_):
        """Return the filter's pattern specified by filter id"""
        return self._filters[id_][1].pattern()

    def addFilter(self, cols, patternSyntax=QRegExp.FixedString, cs=None):
        """Add new filter into proxy model.
        :param cols: a list contains columns to be filtered
        :param cs: Qt.CaseSensitivity, if None then use model's setting
        :return: the id of new filter; id starts from zero"""
        assert patternSyntax in [QRegExp.FixedString, QRegExp.Wildcard,
                                 QRegExp.WildcardUnix, QRegExp.RegExp], 'wrong pattern syntax'
        f = (tuple(cols), QRegExp('', self.filterCaseSensitivity() if cs is None else cs,
                                  patternSyntax))
        try:
            idx = self._filters.index(None)
            self._filters[idx] = f
        except ValueError:
            idx = len(self._filters)
            self._filters.append(f)
        return idx

    def removeFilter(self, id_):
        """Remove the filter specified by its id."""
        assert self._filters[id_]
        self._filters[id_] = None


class DragScrollMixin:
    """Drag & Scroll, like on touchscreens. Implemented only vertical direction."""
    def __init__(self):
        self.__lastPos = None
        self.__disToStart = None  # None --> 10 --> 0 -> None

    def mousePressEvent(self, __):
        self.__disToStart = 5

    def mouseMoveEvent(self, event):
        if self.__lastPos is None:
            self.__lastPos = event.pos()
            return

        delta = event.pos() - self.__lastPos
        if self.__disToStart == 0:
            barV = self.verticalScrollBar()
            barV.setValue(barV.value() - delta.y())
        else:
            self.__disToStart = max(self.__disToStart-abs(delta.y()), 0)
        self.__lastPos = event.pos()

    def mouseReleaseEvent(self, event):
        if self.__disToStart is not None and self.__disToStart > 0:
            ev = QMouseEvent(QEvent.MouseButtonPress, event.pos(),
                             event.globalPos(), Qt.LeftButton,
                             Qt.LeftButton, Qt.NoModifier)
            super().mousePressEvent(ev)
        self.__lastPos = self.__disToStart = None
