import logging
from PySide.QtCore import *
from PySide.QtGui import *
from hazama.ui import setStdEditMenuIcons, makeQIcon, fixWidgetSizeOnHiDpi
from hazama.ui.customobjects import TextFormatter, NTextDocument


class QLineEditWithMenuIcon(QLineEdit):
    """A QLineEdit with system theme icons in context-menu"""
    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        setStdEditMenuIcons(menu)
        menu.exec_(event.globalPos())
        menu.deleteLater()


class MultiLineElideLabel(QFrame):
    ElideMark = '\u2026'
    """Qt Widget version of QML text.maximumLineCount."""

    def __init__(self, *args, **kwargs):
        self._forceHeightHint = kwargs.pop('forceHeightHint', False)
        super().__init__(*args, **kwargs)
        self._maximumLineCount = 4
        self._layout = QTextLayout()
        self._layout.setCacheEnabled(True)
        self._text = None
        self._elideMarkWidth = None
        self._elideMarkPos = None
        self._heightHint = 0
        self._lineHeight = 0
        self._realHeight = 0
        self._updateSize()

    def resizeEvent(self, event):
        self._setupTextLayout()
        super().resizeEvent(event)

    def setFont(self, f):
        super().setFont(f)
        self._updateSize()
        self._setupTextLayout()

    def sizeHint(self):
        __, top, __, bottom = self.getContentsMargins()
        return QSize(-1, self._realHeight + top + bottom)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.translate(self.contentsRect().topLeft())

        self._layout.draw(painter, QPoint())

        if self._elideMarkPos is not None:
            painter.drawText(self._elideMarkPos, self.ElideMark)

    def _updateSize(self):
        # use height because leading is not included
        # this make realHeight equals heightHint even if font fallback happen
        self._lineHeight = self.fontMetrics().height()
        self._heightHint = self._lineHeight * self._maximumLineCount
        self._elideMarkWidth = self.fontMetrics().width(self.ElideMark)
        if self._forceHeightHint:
            self._realHeight = self._heightHint

    def setText(self, text):
        self._text = text.replace('\n', '\u2028')
        self._setupTextLayout()

    def _setupTextLayout(self):
        layout = self._layout
        layout.clearLayout()
        layout.setFont(self.font())

        if not self._text or self._maximumLineCount == 0:
            if self._realHeight != 0 and not self._forceHeightHint:
                self.updateGeometry()
                self._realHeight = 0
            return

        lineWidthLimit = self.contentsRect().width()
        layout.setText(self._text)

        height = 0
        visibleTextLen = 0
        linesLeft = self._maximumLineCount
        self._elideMarkPos = None

        layout.beginLayout()
        while True:
            line = layout.createLine()
            if not line.isValid():
                break  # call methods of invalid one will segfault

            line.setLineWidth(lineWidthLimit)
            visibleTextLen += line.textLength()
            line.setPosition(QPointF(0, height))
            height += line.height()

            linesLeft -= 1
            if linesLeft == 0:
                if visibleTextLen < len(self._text):
                    # ignore right to left text
                    line.setLineWidth(lineWidthLimit - self._elideMarkWidth)
                    self._elideMarkPos = QPoint(line.naturalTextWidth(),
                                                height-line.height()+self.fontMetrics().ascent())

                break
        layout.endLayout()
        height = int(height)
        if height != self._realHeight and not self._forceHeightHint:
            self.updateGeometry()
            self._realHeight = height

    def setMaximumLineCount(self, lines):
        """0 means unlimited."""
        if lines == self._maximumLineCount:
            return
        self._maximumLineCount = lines
        self._setupTextLayout()
        self._updateSize()


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
        # used by tab indent shortcut
        if QLocale().language() in (QLocale.Chinese, QLocale.Japanese):
            self._indent = '　　'   # 2 full width spaces
        else:
            self._indent = '    '  # 4 spaces
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

    def keyPressEvent(self, event):
        if self.isReadOnly():
            return super().keyPressEvent(event)

        if event.modifiers() == Qt.ControlModifier and event.key() in self.key2act:
            # set actions before calling format methods
            self._setFmtActs()
            self.key2act[event.key()].trigger()
        elif event.key() == Qt.Key_Tab:
            # will not receive event if tabChangesFocus is True
            self.textCursor().insertText(self._indent)
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
        else:
            super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        """Disable some unsupported types"""
        self.insertHtml(source.html() or source.text())

    def setRichText(self, text, formats):
        self._doc.setHlColor(self.HlColor)
        self._doc.setText(text, formats)

    def setAutoIndent(self, enabled):
        assert isinstance(enabled, (bool, int))
        self.autoIndent = enabled

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

    @classmethod
    def getDateTime(cls, dt, displayFmt, parent):
        """Show a model datetime dialog, let user change it.
        :param parent: parent widget
        :param dt: datetime to change
        :param displayFmt: the Qt datetime format that used to display
        :return: None if canceled else datetime"""
        dialog = cls(dt, displayFmt, parent)
        ret = dialog.exec_()
        dialog.deleteLater()
        return dialog.dtEdit.dateTime() if ret else None


class FontSelectButton(QPushButton):
    """Select fonts with QFontDialog."""
    PreviewText = 'AaBbYy@2017'

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dialog = None
        self.userSet = None  # whether the font is set by user
        self.configName = None
        self.resettable = False  # display "reset to default" button in dialog
        self.clicked.connect(self._showDialog)

    def setFont(self, font_, userSet=True):
        """Set Font Button's text and font"""
        super().setFont(font_)
        self.userSet = userSet
        family = font_.family() if font_.exactMatch() else QFontInfo(font_).family()
        self.setText('%s %spt' % (family, font_.pointSize()))

    def _showDialog(self):
        dlg = self._dialog = QFontDialog(self)
        dlg.setCurrentFont(self.font())
        fixWidgetSizeOnHiDpi(dlg)

        # set sample text and add button with some hack
        try:
            sample = dlg.findChildren(QLineEdit)[3]
            sample.setText(self.PreviewText)

            if self.resettable:
                box = dlg.findChildren(QDialogButtonBox)[0]
                box.addButton(QDialogButtonBox.RestoreDefaults)
                box.clicked.connect(self._onFontDialogBtnClicked)
        except Exception as e:
            logging.warning('failed to hack Qt font dialog: %s' % e)

        ret = dlg.exec_()
        if ret:
            self.setFont(dlg.selectedFont(), userSet=True)
        self._dialog = None

    def _onFontDialogBtnClicked(self, btn):
        if btn.parent().buttonRole(btn) == QDialogButtonBox.ResetRole:
            assert self.resettable
            self._dialog.reject()
            self.setFont(qApp.font(), userSet=False)
