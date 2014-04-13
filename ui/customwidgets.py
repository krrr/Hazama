from PySide.QtCore import *
from PySide.QtGui import *
from .customobjects import TextFormatter, NTextDocument


class NTextEdit(QTextEdit, TextFormatter):
    """The widget used to edit diary contents in Editor window."""
    def __init__(self, *args, **kwargs):
        super(NTextEdit, self).__init__(*args, **kwargs)
        prt = self.palette()
        prt.setColor(prt.Highlight, QColor(180, 180, 180))
        prt.setColor(prt.HighlightedText, QColor(0, 0, 0))
        self.setPalette(prt)
        self.autoIndent = False
        self.setTabChangesFocus(True)
        # create format menu
        self.submenu = QMenu(self.tr('Format'), self)
        self.hlAct = QAction(QIcon(':/fmt/highlight.png'), self.tr('Highlight'),
                             self, shortcut=QKeySequence('Ctrl+H'))
        self.soAct = QAction(QIcon(':/fmt/strikeout.png'), self.tr('Strike out'),
                             self, shortcut=QKeySequence('Ctrl+-'))
        self.bdAct = QAction(QIcon(':/fmt/bold.png'), self.tr('Bold'),
                             self, shortcut=QKeySequence.Bold)
        self.ulAct = QAction(QIcon(':/fmt/underline.png'), self.tr('Underline'),
                             self, shortcut=QKeySequence.Underline)
        self.itaAct = QAction(QIcon(':/fmt/italic.png'), self.tr('Italic'),
                              self, shortcut=QKeySequence.Italic)
        self.hlAct.triggered.connect(self.setHL)
        self.soAct.triggered.connect(self.setSO)
        self.bdAct.triggered.connect(self.setBD)
        self.ulAct.triggered.connect(self.setUL)
        self.itaAct.triggered.connect(self.setIta)
        for a in (self.hlAct, self.bdAct, self.soAct, self.bdAct,
                  self.ulAct, self.itaAct):
            self.addAction(a)
            self.submenu.addAction(a)
            a.setCheckable(True)
        self.submenu.addSeparator()
        self.clrAct = QAction(self.tr('Clear format'), self,
                              shortcut=QKeySequence('Ctrl+D'))
        self.addAction(self.clrAct)
        self.submenu.addAction(self.clrAct)
        self.clrAct.triggered.connect(self.clearFormat)
        self.menu = self.createStandardContextMenu()
        before = self.menu.actions()[2]
        self.menu.insertSeparator(before)
        self.menu.insertMenu(before, self.submenu)

    def setText(self, text, formats):
        doc = NTextDocument(self)
        doc.setText(text, formats)
        doc.clearUndoRedoStacks()
        doc.setModified(False)
        self.setDocument(doc)

    def setAutoIndent(self, enabled):
        assert isinstance(enabled, (bool, int))
        self.autoIndent = enabled

    def contextMenuEvent(self, event):
        cur = self.textCursor()
        if cur.hasSelection():
            curtfmt = cur.charFormat()
            self.hlAct.setChecked(curtfmt.background().color() == self.hl_color)
            self.bdAct.setChecked(curtfmt.fontWeight() == QFont.Bold)
            self.soAct.setChecked(curtfmt.fontStrikeOut())
            self.ulAct.setChecked(curtfmt.fontUnderline())
            self.itaAct.setChecked(curtfmt.fontItalic())
            self.submenu.setEnabled(True)
        else:
            self.submenu.setEnabled(False)
        self.menu.exec_(event.globalPos())

    def clearFormat(self):
        fmt = QTextCharFormat()
        self.textCursor().setCharFormat(fmt)

    def keyPressEvent(self, event):
        """Auto-indent support"""
        if event.key() == Qt.Key_Return and self.autoIndent:
            spacecount = 0
            cur = self.textCursor()
            savedpos = cur.position()
            cur.movePosition(QTextCursor.StartOfBlock)
            cur.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            while cur.selectedText() == ' ':
                spacecount += 1
                cur.clearSelection()
                cur.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)

            cur.setPosition(savedpos)
            super(NTextEdit, self).keyPressEvent(event)
            cur.insertText(' ' * spacecount)
        else:
            return super(NTextEdit, self).keyPressEvent(event)

    def insertFromMimeData(self, source):
        """Disable some unsupported types"""
        self.insertHtml(source.html() or source.text())


class SearchBox(QLineEdit):
    def __init__(self, parent=None):
        super(SearchBox, self).__init__(parent)

        self.button = QToolButton(self)
        self.button.setFixedSize(18, 18)
        self.button.setCursor(Qt.ArrowCursor)
        self.button.clicked.connect(self.clear)

        self.textChanged.connect(self.update)
        self.setPlaceholderText(self.tr('Search'))
        self.setTextMargins(QMargins(2, 0, 20, 0))
        self.update('')

    def resizeEvent(self, event):
        w, h = event.size().toTuple()
        pos_y = (h - 18) / 2
        self.button.move(w - 18 - pos_y, pos_y)

    def update(self, text):
        iconame = 'search_clr' if text else 'search'
        fontstyle = 'normal' if text else 'italic'
        self.button.setStyleSheet('QToolButton{border: none;'
                                  'background: url(:/images/%s.png);'
                                  'background-position: center}' % iconame)
        self.setStyleSheet('QLineEdit{font-style: %s}' % fontstyle)


class DateTimeDialog(QDialog):
    timeFmt = "yyyy-MM-dd HH:mm"

    def __init__(self, timestr, parent=None):
        super(DateTimeDialog, self).__init__(parent, Qt.WindowTitleHint)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr('Edit datetime'))
        self.setMinimumWidth(100)
        self.verticalLayout = QVBoxLayout(self)
        dt = QDateTime.fromString(timestr, self.timeFmt)
        self.dtEdit = QDateTimeEdit(dt)
        self.dtEdit.setDisplayFormat(self.timeFmt)
        self.verticalLayout.addWidget(self.dtEdit)
        self.btnBox = QDialogButtonBox()
        self.btnBox.setOrientation(Qt.Horizontal)
        self.btnBox.setStandardButtons(QDialogButtonBox.Ok |
                                       QDialogButtonBox.Cancel)
        self.verticalLayout.addWidget(self.btnBox)
        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)

    @staticmethod
    def getDateTime(timestr, parent):
        """Run Dialog,return None if canceled,otherwise return timestr"""
        dialog = DateTimeDialog(timestr, parent)
        ret = dialog.exec_()
        return dialog.dtEdit.dateTime().toString(dialog.timeFmt) if ret else None



