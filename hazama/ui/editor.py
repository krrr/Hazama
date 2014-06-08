from PySide.QtGui import *
from PySide.QtCore import *
from ui.editor_ui import Ui_Editor
from ui.customobjects import TagCompleter
from ui.customwidgets import DateTimeDialog
from ui import font, dt_trans, currentdt_str
from config import settings, nikki


class Editor(QWidget, Ui_Editor):
    """Widget used to edit diary's body,title,tag,datetime.
    Signal closed: (editorId, nikkiId, tagsModified),nikkiId is -1
    if canceled or no need to save.
    """
    closed = Signal(int, int, bool)

    def __init__(self, editorId, new, row, parent=None):
        super(Editor, self).__init__(parent, Qt.Window)
        self.setupUi(self)
        self.id, self.new = editorId, new
        geo = settings['Editor'].get('windowgeo')
        self.restoreGeometry(QByteArray.fromHex(geo))
        # setup textEditor and titleEditor, set window title
        if not new:
            self.datetime = row['datetime']
            self.titleEditor.setText(row['title'])
            self.textEditor.setText(row['text'], row['formats'])
        else:
            self.datetime = None
        self.textEditor.setFont(font.text)
        self.textEditor.setAutoIndent(settings['Editor'].getint('autoindent', 1))
        self.titleEditor.setFont(font.title)
        title = ((row['title'] if row else None) or
                (dt_trans(self.datetime).split()[0] if self.datetime else None) or
                 self.tr('New Diary'))
        self.setWindowTitle("%s - Hazama" % title)
        # setup datetime display
        self.dtLabel.setText('' if self.datetime is None
                             else dt_trans(self.datetime))
        self.dtLabel.setFont(font.date)
        sz = min(font.date_m.ascent(), 16)
        self.dtBtn.setIconSize(QSize(sz, sz))
        # set up tagEditor
        self.updateTagEditorFont('')
        if not new:
            tags = row['tags']
            self.tagEditor.setText(' '.join(tags) if tags else '')
        completer = TagCompleter(nikki.gettag(), self.tagEditor)
        self.tagEditor.setCompleter(completer)
        self.timeModified = self.tagModified = False
        # setup shortcuts
        self.closeSaveSc = QShortcut(QKeySequence.Save, self)
        self.closeSaveSc.activated.connect(self.close)
        self.closeSaveSc2 = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.closeSaveSc2.activated.connect(self.close)
        self.preSc = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_PageUp), self)
        self.nextSc = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_PageDown), self)

    def closeEvent(self, event):
        """Save geometry information and diary"""
        settings['Editor']['windowgeo'] = str(self.saveGeometry().toHex())
        nikkiId = self.saveNikki()
        self.closed.emit(self.id, nikkiId, self.tagModified)
        event.accept()

    def closeNoSave(self):
        settings['Editor']['windowgeo'] = str(self.saveGeometry().toHex())
        self.hide()  # use deleteLater to free, not destroy slot or attribute
        self.closed.emit(self.id, -1, False)

    def saveNikki(self):
        """Save if changed and return nikkiId,else return -1"""
        if (self.textEditor.document().isModified() or
           self.titleEditor.isModified() or self.timeModified or
           self.tagModified):
            if self.datetime is None:
                self.datetime = currentdt_str()
            if self.tagModified:
                tags = list(set(self.tagEditor.text().split()))
            else:
                tags = None
            # realId: id returned by database
            realId = nikki.save(id=self.id, datetime=self.datetime,
                                formats=self.textEditor.getFormats(),
                                text=self.textEditor.toPlainText(),
                                title=self.titleEditor.text(),
                                tags=tags, new=self.new)
            return realId
        else:
            return -1

    @Slot()
    def on_tagEditor_textEdited(self):
        # tagEditor.isModified() will be reset by completer.So this instead.
        self.tagModified = True

    @Slot()
    def on_dtBtn_clicked(self):
        """Show datetime edit dialog"""
        dt = currentdt_str() if self.datetime is None else self.datetime
        new_dt = DateTimeDialog.getDateTime(dt, self)
        if new_dt is not None and new_dt != self.datetime:
            self.datetime = new_dt
            self.dtLabel.setText(dt_trans(new_dt))
            self.timeModified = True

    def showEvent(self, event):
        if settings['Editor'].getint('titlefocus', 0):
            self.titleEditor.setCursorPosition(0)
        else:
            self.textEditor.setFocus()
            self.textEditor.moveCursor(QTextCursor.Start)

    def updateTagEditorFont(self, text):
        """Set tagEditor's placeHolderFont to italic"""
        style = 'normal' if text else 'italic'
        self.tagEditor.setStyleSheet('font-style: %s' % style)


