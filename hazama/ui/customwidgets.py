from PySide.QtCore import *
from PySide.QtGui import *
from hazama.ui import setStdEditMenuIcons, makeQIcon
from hazama.ui.customobjects import TextFormatter, NTextDocument


class QLineEditWithMenuIcon(QLineEdit):
    """A QLineEdit with system theme icons in context-menu"""
    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        setStdEditMenuIcons(menu)
        menu.exec_(event.globalPos())
        menu.deleteLater()


class NDocumentLabel(QFrame):
    """Simple widget to draw QTextDocument. sizeHint will always related
    to fixed number of lines set. If font fallback happen, it may look bad."""

    def __init__(self, parent=None, lines=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._lines = self._heightHint = None
        self.doc = NTextDocument(self)
        self.doc.setDocumentMargin(0)
        self.doc.setUndoRedoEnabled(False)
        self.setLines(lines if lines else 4)
        self.doc.documentLayout().setPaintDevice(self)  # make difference on high DPI

    def setFont(self, f):
        self.doc.setDefaultFont(f)
        super().setFont(f)
        self.setLines(self._lines)  # refresh size hint

    def setText(self, text, formats):
        self.doc.setText(text, formats)
        # delete exceed lines here using QTextCursor will slow down

    def setLines(self, lines):
        self._lines = lines
        self.doc.setText('\n' * (lines - 1), None)
        self._heightHint = int(self.doc.size().height())
        self.updateGeometry()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.contentsRect()
        painter.translate(rect.topLeft())
        rect.moveTo(0, 0)  # become clip rect
        self.doc.drawContentsPalette(painter, rect, self.palette())

    def resizeEvent(self, event):
        self.doc.setTextWidth(self.contentsRect().width())
        super().resizeEvent(event)

    def sizeHint(self):
        __, top, __, bottom = self.getContentsMargins()
        return QSize(-1, self._heightHint + top + bottom)


class NTextEdit(QTextEdit, TextFormatter):
    """The widget used to edit diary contents in Editor window."""
    # spaces that auto-indent can recognize
    SPACE_KINDS = (' ', '\u3000')  # full width space U+3000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._doc = NTextDocument(self)
        self.setDocument(self._doc)
        # remove highlight color's alpha to avoid alpha loss in copy&paste.
        # NTextDocument should use this color too.
        hl, bg = self.HlColor, self.palette().base().color()
        fac = hl.alpha() / 255
        self.HlColor = QColor(round(hl.red()*fac + bg.red()*(1-fac)),
                              round(hl.green()*fac + bg.green()*(1-fac)),
                              round(hl.blue()*fac + bg.blue()*(1-fac)))

        self.autoIndent = False
        self.setTabChangesFocus(True)
        # setup format menu
        onHLAct = lambda: super(NTextEdit, self).setHL(self.hlAct.isChecked())
        onBDAct = lambda: super(NTextEdit, self).setBD(self.bdAct.isChecked())
        onSOAct = lambda: super(NTextEdit, self).setSO(self.soAct.isChecked())
        onULAct = lambda: super(NTextEdit, self).setUL(self.ulAct.isChecked())
        onItaAct = lambda: super(NTextEdit, self).setIta(self.itaAct.isChecked())

        self.fmtMenu = QMenu(self.tr('Format'), self)
        # shortcuts of format actions only used to display shortcut-hint in menu
        self.hlAct = QAction(makeQIcon(':/menu/highlight.png'), self.tr('Highlight'),
                             self, triggered=onHLAct,
                             shortcut=QKeySequence('Ctrl+H'))
        self.bdAct = QAction(makeQIcon(':/menu/bold.png'), self.tr('Bold'),
                             self, triggered=onBDAct,
                             shortcut=QKeySequence.Bold)
        self.soAct = QAction(makeQIcon(':/menu/strikeout.png'), self.tr('Strike out'),
                             self, triggered=onSOAct,
                             shortcut=QKeySequence('Ctrl+T'))
        self.ulAct = QAction(makeQIcon(':/menu/underline.png'), self.tr('Underline'),
                             self, triggered=onULAct,
                             shortcut=QKeySequence.Underline)
        self.itaAct = QAction(makeQIcon(':/menu/italic.png'), self.tr('Italic'),
                              self, triggered=onItaAct,
                              shortcut=QKeySequence.Italic)
        self.clrAct = QAction(self.tr('Clear format'), self,
                              shortcut=QKeySequence('Ctrl+D'),
                              triggered=self.clearFormat)
        self.acts = (self.hlAct, self.bdAct, self.soAct, self.ulAct,
                     self.itaAct)  # excluding uncheckable clrAct
        for a in self.acts:
            self.fmtMenu.addAction(a)
            a.setCheckable(True)
        self.fmtMenu.addSeparator()
        self.addAction(self.clrAct)
        self.fmtMenu.addAction(self.clrAct)
        self.key2act = {
            Qt.Key_H: self.hlAct, Qt.Key_B: self.bdAct, Qt.Key_T: self.soAct,
            Qt.Key_U: self.ulAct, Qt.Key_I: self.itaAct}

    def setRichText(self, text, formats):
        self._doc.setHlColor(self.HlColor)
        self._doc.setText(text, formats)

    def setAutoIndent(self, enabled):
        assert isinstance(enabled, (bool, int))
        self.autoIndent = enabled

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        setStdEditMenuIcons(menu)

        if not self.isReadOnly():
            if self.textCursor().hasSelection():
                self._setFmtActs()
                self.fmtMenu.setEnabled(True)
            else:
                self.fmtMenu.setEnabled(False)
            before = menu.actions()[2]
            menu.insertSeparator(before)
            menu.insertMenu(before, self.fmtMenu)

        menu.exec_(event.globalPos())
        menu.deleteLater()

    def getRichText(self):
        # self.document() will return QTextDocument, not NTextDocument
        return self.toPlainText(), self._doc.getFormats()

    def _setFmtActs(self):
        """Check formats in current selection and check or uncheck actions"""
        fmts = [QTextFormat.BackgroundBrush, QTextFormat.FontWeight,
                QTextFormat.FontStrikeOut,
                QTextFormat.TextUnderlineStyle, QTextFormat.FontItalic]

        cur = self.textCursor()
        start, end = cur.anchor(), cur.position()
        if start > end:
            start, end = end, start
        results = [True] * 5
        for pos in range(end, start, -1):
            cur.setPosition(pos)
            charFmt = cur.charFormat()
            for i, f in enumerate(fmts):
                if results[i] and not charFmt.hasProperty(f):
                    results[i] = False
            if not any(results): break
        for i, c in enumerate(results):
            self.acts[i].setChecked(c)

    def clearFormat(self):
        fmt = QTextCharFormat()
        self.textCursor().setCharFormat(fmt)

    def keyPressEvent(self, event):
        if (event.modifiers() == Qt.ControlModifier and not self.isReadOnly() and
           event.key() in self.key2act):
            # set actions before calling format methods
            self._setFmtActs()
            self.key2act[event.key()].trigger()
            event.accept()
        elif event.key() == Qt.Key_Return and self.autoIndent:
            # auto-indent support
            para = self.textCursor().block().text()
            if len(para) > 0 and para[0] in NTextEdit.SPACE_KINDS:
                space, spaceCount = para[0], 1
                for c in para[1:]:
                    if c != space: break
                    spaceCount += 1
                super().keyPressEvent(event)
                self.textCursor().insertText(space * spaceCount)
            else:
                super().keyPressEvent(event)
            event.accept()
        else:
            super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        """Disable some unsupported types"""
        self.insertHtml(source.html() or source.text())


class NLineEditMouse(QLineEditWithMenuIcon):
    """QLineEdit that ignore mouse back/forward button, with menu icon."""
    def mousePressEvent(self, event):
        if event.button() in (Qt.XButton1, Qt.XButton2):
            event.ignore()
        else:
            super().mousePressEvent(event)


class NElideLabel(QLabel):
    elideMode = Qt.ElideRight

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.contentsRect()
        t = self.fontMetrics().elidedText(self.text(), self.elideMode, rect.width())
        painter.drawText(rect, self.alignment(), t)

    def minimumSizeHint(self):
        return QSize()  # return invalid size


class DateTimeDialog(QDialog):
    """A dialog that let user change datetime, just like QColorDialog."""
    def __init__(self, dt, displayFmt, parent=None):
        super().__init__(parent, Qt.WindowTitleHint)
        self.format = displayFmt
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr('Edit datetime'))
        self.setMinimumWidth(100)
        self.verticalLayout = QVBoxLayout(self)
        self.dtEdit = QDateTimeEdit(dt, self)
        self.dtEdit.setDisplayFormat(displayFmt)
        self.verticalLayout.addWidget(self.dtEdit)
        self.btnBox = QDialogButtonBox(self)
        self.btnBox.setOrientation(Qt.Horizontal)
        self.btnBox.setStandardButtons(QDialogButtonBox.Ok |
                                       QDialogButtonBox.Cancel)
        self.verticalLayout.addWidget(self.btnBox)
        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)

    @staticmethod
    def getDateTime(dt, displayFmt, parent):
        """Show a model datetime dialog, let user change it.
        :param parent: parent widget
        :param dt: datetime to change
        :param displayFmt: the Qt datetime format that used to display
        :return: None if canceled else datetime"""
        dialog = DateTimeDialog(dt, displayFmt, parent)
        ret = dialog.exec_()
        dialog.deleteLater()
        return dialog.dtEdit.dateTime() if ret else None
