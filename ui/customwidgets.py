from PySide.QtCore import *
from PySide.QtGui import *
from .customobjects import TextFormatter, NTextDocument
from html.parser import HTMLParser
import re


class NTextEdit(QTextEdit, TextFormatter):
    """The widget used to edit diary contents in Editor window."""
    def __init__(self, *args, **kwargs):
        super(NTextEdit, self).__init__(*args, **kwargs)
        # setup colors
        prt = self.palette()
        prt.setColor(prt.Highlight, QColor(180, 180, 180))
        prt.setColor(prt.HighlightedText, QColor(0, 0, 0))
        self.setPalette(prt)
        # remove highlight color's alpha to avoid alpha loss in copy&paste.
        # NTextDocument should use this color too.
        hl, bg = self.HlColor, prt.base().color()
        fac = hl.alpha() / 255
        self.HlColor = QColor(round(hl.red()*fac + bg.red()*(1-fac)),
                              round(hl.green()*fac + bg.green()*(1-fac)),
                              round(hl.blue()*fac + bg.blue()*(1-fac)))
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
        doc.setHlColor(self.HlColor)
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
            curtFmt = cur.charFormat()
            self.hlAct.setChecked(curtFmt.background().color() == self.HlColor)
            self.bdAct.setChecked(curtFmt.fontWeight() == QFont.Bold)
            self.soAct.setChecked(curtFmt.fontStrikeOut())
            self.ulAct.setChecked(curtFmt.fontUnderline())
            self.itaAct.setChecked(curtFmt.fontItalic())
            self.submenu.setEnabled(True)
        else:
            self.submenu.setEnabled(False)
        self.menu.exec_(event.globalPos())

    def getFormats(self):
        parser = QtHtmlParser()
        return parser.feed(self.toHtml())

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
    """A real-time search box"""
    def __init__(self, parent=None):
        super(SearchBox, self).__init__(parent)
        self.setMinimumHeight(23)  # looks fine when toolbar icon is 24x24
        self.setTextMargins(QMargins(2, 0, 20, 0))
        self.button = QToolButton(self)
        self.button.setFixedSize(18, 18)
        self.button.setCursor(Qt.ArrowCursor)
        self.button.clicked.connect(self.clear)
        self.textChanged.connect(self.update)
        self.retranslate()
        self.text_before_bool = True
        self.update('')

    def resizeEvent(self, event):
        w, h = event.size().toTuple()
        pos_y = (h - 18) / 2
        self.button.move(w - 18 - pos_y, pos_y)

    def update(self, text):
        """Update button icon and PlaceholderText font style"""
        if self.text_before_bool == bool(text): return
        ico_name = 'search_clr' if text else 'search'
        font_style = 'normal' if text else 'italic'
        self.button.setStyleSheet('QToolButton{border: none;'
                                  'background: url(:/images/%s.png);'
                                  'background-position: center}' % ico_name)
        self.setStyleSheet('QLineEdit{font-style: %s}' % font_style)
        self.text_before_bool = bool(text)

    def retranslate(self):
        self.setPlaceholderText(self.tr('Search'))


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

