from PySide.QtGui import *
from PySide.QtCore import *
from ui.editor_ui import Ui_editor
from ui.customobjects import TagCompleter
from ui.customwidgets import DateTimeDialog
from ui import font, datetimeTrans, currentDatetime, datetimeFmt
from config import settings, nikki


class Editor(QWidget, Ui_editor):
    """Widget used to edit diary's body,title,tag,datetime.
    Signal closed: (id of nikki, needSave),
    """
    closed = Signal(int, bool)

    def __init__(self, parent=None):
        super(Editor, self).__init__(parent)
        self.setupUi(self)
        self.datetime = self.id = None
        geo = settings['Editor'].get('windowgeo')
        self.restoreGeometry(QByteArray.fromHex(geo))
        # setup textEditor and titleEditor, set window title
        self.textEditor.setFont(font.text)
        self.textEditor.setAutoIndent(settings['Editor'].getint('autoindent', 1))
        self.titleEditor.setFont(font.title)
        # setup datetime display
        self.dtLabel.setFont(font.date)
        sz = min(font.date_m.ascent(), 16)
        self.dtBtn.setIconSize(QSize(sz, sz))
        # set up tagEditor
        self.tagEditor.setTextMargins(QMargins(2, 0, 2, 0))
        completer = TagCompleter(nikki.gettag(), self.tagEditor)
        self.tagEditor.setCompleter(completer)
        self.timeModified = self.tagModified = False
        # setup shortcuts
        # seems PySide has problem with QKeySequence.StandardKeys
        self.closeSaveSc = QShortcut(QKeySequence.Save, self, self.close)
        self.closeNoSaveSc = QShortcut(QKeySequence('Ctrl+W'), self, self.closeNoSave)
        # QKeySequence.PreviousChild(Ctrl+Shift+Backtab) doesn't work
        self.preSc = QShortcut(QKeySequence('Ctrl+Shift+Tab'), self)
        self.nextSc = QShortcut(QKeySequence('Ctrl+Tab'), self)

    def closeEvent(self, event):
        settings['Editor']['windowgeo'] = str(self.saveGeometry().toHex())
        needSave = (self.textEditor.document().isModified() or
                    self.titleEditor.isModified() or self.timeModified or
                    self.tagModified)
        self.closed.emit(self.id, needSave)
        event.accept()

    def closeNoSave(self):
        settings['Editor']['windowgeo'] = str(self.saveGeometry().toHex())
        self.hide()  # use deleteLater to free, not destroy slot or DeleteOnClose attribute
        self.closed.emit(self.id, False)

    @Slot()
    def on_tagEditor_textEdited(self):
        # tagEditor.isModified() will be reset by completer. So this instead.
        self.tagModified = True

    @Slot()
    def on_dtBtn_clicked(self):
        """Show datetime edit dialog"""
        dtStr = currentDatetime() if self.datetime is None else self.datetime
        locale = QLocale()
        dbDatetimeFmt = 'yyyy-MM-dd HH:mm'
        dt = locale.toDateTime(dtStr, dbDatetimeFmt)
        new_dt = DateTimeDialog.getDateTime(dt, datetimeFmt, self)
        if new_dt is not None:
            new_dtStr = new_dt.toString(dbDatetimeFmt)
            if new_dtStr != self.datetime:
                self.datetime = new_dtStr
                self.dtLabel.setText(datetimeTrans(new_dtStr))
                self.timeModified = True

    def showEvent(self, event):
        title = (self.titleEditor.text() or
                 (datetimeTrans(self.datetime, forceDateOnly=True) if self.datetime else None) or
                 self.tr('New Diary'))
        self.setWindowTitle("%s - Hazama" % title)
        self.dtLabel.setText('' if self.datetime is None
                             else datetimeTrans(self.datetime))
        if settings['Editor'].getint('titlefocus', 0):
            self.titleEditor.setCursorPosition(0)
        else:
            self.textEditor.setFocus()
            self.textEditor.moveCursor(QTextCursor.Start)
        event.accept()

