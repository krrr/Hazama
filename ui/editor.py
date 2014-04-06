from PySide.QtGui import *
from PySide.QtCore import *
from .editor_ui import Ui_Editor
from .customobjects import TagCompleter
from .customwidgets import DateTimeDialog
from . import font, dt_trans, currentdt_str
from config import settings, nikki


class Editor(QWidget, Ui_Editor):
    '''Widget used to edit diary's body,title,tag,datetime.
    Signal closed: (editorid, nikkiid, tagsModified),nikkiid is -1
    if canceled or no need to save.
    '''
    closed = Signal(int, int, bool)
    def __init__(self, new, row):
        super(Editor, self).__init__()
        self.setupUi(self)
        self.new = new
        geo = settings['Editor'].get('windowgeo')
        self.restoreGeometry(QByteArray.fromHex(geo))
        # setup texteditor and titleeditor, set window title
        if not new:
            self.datetime = row['datetime']
            self.titleEditor.setText(row['title'])
            formats = None if row['plaintext'] else nikki.getformat(row['id'])
            self.textEditor.setText(row['text'], formats)
        else:
            self.datetime = None
        self.textEditor.setFont(font.text)
        self.textEditor.setAutoIndent(settings['Editor'].getint('autoindent', 1))
        self.titleEditor.setFont(font.title)
        titlehint = (row['title'] if row else None) or \
                    (dt_trans(self.datetime,True) if self.datetime else None) or \
                    self.tr('New Diary')
        self.setWindowTitle("%s - Hazama" % titlehint)
        # setup datetime display
        self.dtLabel.setText('' if self.datetime is None
                             else dt_trans(self.datetime))
        self.dtLabel.setFont(font.date)
        self.dtBtn.setIcon(QIcon(':/editor/clock.png'))
        sz = min(font.date_m.ascent(), 16)
        self.dtBtn.setIconSize(QSize(sz, sz))
        # set up tageditor
        self.updateTagEditorFont('')
        if not new: self.tagEditor.setText(row['tags'])
        completer = TagCompleter(nikki.gettag(), self)
        self.tagEditor.setCompleter(completer)
        self.timeModified = self.tagsModified = False
        # setup shortcuts
        self.closeSaveSc = QShortcut(QKeySequence.Save, self)
        self.closeSaveSc.activated.connect(self.close)
        self.closeSaveSc2 = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.closeSaveSc2.activated.connect(self.close)
        self.preSc = QShortcut(QKeySequence(Qt.CTRL+Qt.Key_PageUp), self)
        self.nextSc = QShortcut(QKeySequence(Qt.CTRL+Qt.Key_PageDown), self)

    def closeEvent(self, event):
        "Save geometry information and diary"
        settings['Editor']['windowgeo'] = str(self.saveGeometry().toHex())
        nikkiid = self.saveNikki()
        event.accept()
        self.closed.emit(self.id, nikkiid, self.tagsModified)

    def closeNoSave(self):
        settings['Editor']['windowgeo'] = str(self.saveGeometry().toHex())
        self.hide()
        self.closed.emit(self.id, -1, False)

    def saveNikki(self):
        "Save if changed and return nikkiid,else return -1"
        if (self.textEditor.document().isModified() or
        self.titleEditor.isModified() or self.timeModified or
        self.tagsModified):
            if self.datetime is None:
                self.datetime = currentdt_str()
            if self.tagsModified:
                tags = self.tagEditor.text().split()
                tags = list(filter(lambda t: tags.count(t)==1, tags))
            else:
                tags = None
            # realid: id returned by database
            realid = nikki.save(id=self.id, datetime=self.datetime,
                                html=self.textEditor.toHtml(),
                                plaintxt=self.textEditor.toPlainText(),
                                title=self.titleEditor.text(),
                                tags=tags, new=self.new)
            return realid
        else:
            return -1

    @Slot()
    def on_tagEditor_textEdited(self):
        # tageditor.isModified() will be reset by completer.So this instead.
        self.tagsModified = True

    @Slot()
    def on_dtBtn_clicked(self):
        dt = currentdt_str() if self.datetime is None else self.datetime
        new_dt = DateTimeDialog.getDateTime(dt, self)
        if new_dt is not None and new_dt!=self.datetime:
            self.datetime = new_dt
            self.dtLabel.setText(dt_trans(new_dt))
            self.timeModified = True

    def showEvent(self, event):
        if not settings['Editor'].getint('titlefocus', 0):
            self.textEditor.setFocus()
        self.textEditor.moveCursor(QTextCursor.Start)

    def updateTagEditorFont(self, text):
        "Set tagEditor's placeHoderFont to italic"
        fontstyle = 'normal' if text else 'italic'
        self.tagEditor.setStyleSheet('font-style: %s' % fontstyle)

    def setEditorId(self, id):
        self.id = id

