from PySide.QtCore import *
from PySide.QtGui import *
from ui import setStdEditMenuIcons
from ui.customobjects import TextFormatter, NTextDocument
from html.parser import HTMLParser
import re
from config import settings


class QLineEditWithMenuIcon(QLineEdit):
    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        setStdEditMenuIcons(menu)
        menu.exec_(event.globalPos())
        menu.deleteLater()


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
        self.subMenu = QMenu(self.tr('Format'), self)
        # shortcuts of format actions only used to display shortcut-hint in menu
        self.hlAct = QAction(QIcon(':/fmt/highlight.png'), self.tr('Highlight'),
                             self, triggered=self.setHL,
                             shortcut=QKeySequence('Ctrl+H'))
        self.bdAct = QAction(QIcon(':/fmt/bold.png'), self.tr('Bold'),
                             self, triggered=self.setBD,
                             shortcut=QKeySequence.Bold)
        self.soAct = QAction(QIcon(':/fmt/strikeout.png'), self.tr('Strike out'),
                             self, triggered=self.setSO,
                             shortcut=QKeySequence('Ctrl+T'))
        self.ulAct = QAction(QIcon(':/fmt/underline.png'), self.tr('Underline'),
                             self, triggered=self.setUL,
                             shortcut=QKeySequence.Underline)
        self.itaAct = QAction(QIcon(':/fmt/italic.png'), self.tr('Italic'),
                              self, triggered=self.setIta,
                              shortcut=QKeySequence.Italic)
        self.clrAct = QAction(self.tr('Clear format'), self,
                              shortcut=QKeySequence('Ctrl+D'),
                              triggered=self.clearFormat)
        self.acts = (self.hlAct, self.bdAct, self.soAct, self.ulAct,
                     self.itaAct)  # excluding uncheckable clrAct
        for a in self.acts:
            self.subMenu.addAction(a)
            a.setCheckable(True)
        self.subMenu.addSeparator()
        self.addAction(self.clrAct)
        self.subMenu.addAction(self.clrAct)
        self.key2act = {
            Qt.Key_H: self.hlAct, Qt.Key_B: self.bdAct, Qt.Key_T: self.soAct,
            Qt.Key_U: self.ulAct, Qt.Key_I: self.itaAct}

    def setText(self, text, formats):
        doc = NTextDocument(self)
        doc.setDefaultFont(self.document().defaultFont())
        doc.setDefaultStyleSheet(self.document().defaultStyleSheet())
        doc.setDefaultCursorMoveStyle(self.document().defaultCursorMoveStyle())
        doc.setDefaultTextOption(self.document().defaultTextOption())
        doc.setHlColor(self.HlColor)
        doc.setText(text, formats)
        doc.clearUndoRedoStacks()
        doc.setModified(False)
        self.setDocument(doc)

    def setAutoIndent(self, enabled):
        assert isinstance(enabled, (bool, int))
        self.autoIndent = enabled

    def contextMenuEvent(self, event):
        if self.textCursor().hasSelection():
            self.checkFormats()
            self.subMenu.setEnabled(True)
        else:
            self.subMenu.setEnabled(False)
        menu = self.createStandardContextMenu()
        setStdEditMenuIcons(menu)
        before = menu.actions()[2]
        menu.insertSeparator(before)
        menu.insertMenu(before, self.subMenu)
        menu.exec_(event.globalPos())
        menu.deleteLater()

    def getFormats(self):
        parser = QtHtmlParser()
        return parser.feed(self.toHtml())

    def clearFormat(self):
        fmt = QTextCharFormat()
        self.textCursor().setCharFormat(fmt)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() in self.key2act:
            # set actions before calling format methods
            self.checkFormats()
            self.key2act[event.key()].trigger()
            event.accept()
        elif event.key() == Qt.Key_Return and self.autoIndent:
            # auto-indent support
            spaceCount = 0
            cur = self.textCursor()
            savedPos = cur.position()
            cur.movePosition(QTextCursor.StartOfBlock)
            cur.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            while cur.selectedText() == ' ':
                spaceCount += 1
                cur.clearSelection()
                cur.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            cur.setPosition(savedPos)
            super(NTextEdit, self).keyPressEvent(event)
            cur.insertText(' ' * spaceCount)
            event.accept()
        else:
            super(NTextEdit, self).keyPressEvent(event)

    def insertFromMimeData(self, source):
        """Disable some unsupported types"""
        self.insertHtml(source.html() or source.text())


class SearchBox(QLineEditWithMenuIcon):
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
        self.isTextBefore = True
        self.update('')

    def resizeEvent(self, event):
        w, h = event.size().toTuple()
        pos_y = (h - 18) / 2
        self.button.move(w - 18 - pos_y, pos_y)

    def update(self, text):
        """Update button icon and PlaceholderText font style"""
        if self.isTextBefore == bool(text): return
        ico_name = 'search_clr' if text else 'search'
        self.button.setStyleSheet('QToolButton{border: none;'
                                  'background: url(:/images/%s.png);'
                                  'background-position: center}' % ico_name)
        self.isTextBefore = bool(text)

    def retranslate(self):
        self.setPlaceholderText(self.tr('Search'))


class DateTimeDialog(QDialog):
    timeFmt = "yyyy-MM-dd HH:mm"

    def __init__(self, timeStr, parent=None):
        super(DateTimeDialog, self).__init__(parent, Qt.WindowTitleHint)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr('Edit datetime'))
        self.setMinimumWidth(100)
        self.verticalLayout = QVBoxLayout(self)
        dt = QDateTime.fromString(timeStr, self.timeFmt)
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
    def getDateTime(timeStr, parent):
        """Run Dialog,return None if canceled else time string"""
        dialog = DateTimeDialog(timeStr, parent)
        ret = dialog.exec_()
        dialog.deleteLater()
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


class SortOrderMenu(QMenu):
    """Menu used to Change sort order of NList."""
    orderChanged = Signal()

    def __init__(self, parent=None):
        super(SortOrderMenu, self).__init__(parent)
        self.aboutToShow.connect(self.setActions)
        # create actions
        self.datetime = QAction(self.tr('Date'), self)
        self.datetime.name = 'datetime'
        self.title = QAction(self.tr('Title'), self)
        self.title.name = 'title'
        self.length = QAction(self.tr('Length'), self)
        self.length.name = 'length'
        self.reverse = QAction(self.tr('Reverse'), self)
        self.orders = (self.datetime, self.title, self.length)
        for a in self.orders:
            a.setCheckable(True)
            self.addAction(a)
            a.triggered[bool].connect(self.signalEmitter)
        self.addSeparator()
        self.reverse.setCheckable(True)
        self.addAction(self.reverse)
        self.reverse.triggered[bool].connect(self.signalEmitter)

    def setActions(self):
        """Set actions checked/unchecked before showing"""
        order = settings['Main'].get('listsortby', 'datetime')
        reverse = settings['Main'].getint('listreverse', 1)
        for a in self.orders: a.setChecked(False)
        toEnable = getattr(self, order, self.datetime)
        toEnable.setChecked(True)
        self.reverse.setChecked(reverse)

    def signalEmitter(self, checked):
        """Save new order to settings and emit a signal"""
        sender = self.sender()
        if hasattr(sender, 'name'):
            if checked:
                settings['Main']['listsortby'] = sender.name
                self.orderChanged.emit()
        else:
            settings['Main']['listreverse'] = str(checked.real)
            self.orderChanged.emit()


