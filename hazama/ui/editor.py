from PySide.QtGui import *
from PySide.QtCore import *
from hazama.ui.editor_ui import Ui_editor
from hazama.ui.customobjects import TagCompleter
from hazama.ui.customwidgets import DateTimeDialog
from hazama.ui import font, datetimeTrans, currentDatetime, datetimeFmt
from hazama.config import settings, nikki


class Editor(QWidget, Ui_editor):
    """Widget used to edit diary's body,title,tag,datetime.
    Signal closed: (id of nikki, needSave),
    """
    closed = Signal(int, bool)

    def __init__(self, parent=None):
        super(Editor, self).__init__(parent)
        self.setupUi(self)
        self.datetime = self.id = None
        geo = settings['Editor'].get('windowGeo')
        self.restoreGeometry(QByteArray.fromHex(geo))
        # setup textEditor and titleEditor, set window title
        self.textEditor.setFont(font.text)
        self.textEditor.setAutoIndent(
            settings['Editor'].getboolean('autoIndent', True))
        self.titleEditor.setFont(font.title)
        # setup datetime display
        self.dtLabel.setFont(font.datetime)
        sz = min(font.datetime_m.ascent(), 16)
        self.dtBtn.setIconSize(QSize(sz, sz))
        # set up tagEditor
        self.tagEditor.setTextMargins(QMargins(2, 0, 2, 0))
        completer = TagCompleter(list(nikki.gettags()), self.tagEditor)
        self.tagEditor.setCompleter(completer)
        self.timeModified = self.tagModified = False
        # setup shortcuts
        # seems PySide has problem with QKeySequence.StandardKeys
        self.closeSaveSc = QShortcut(QKeySequence.Save, self, self.close)
        self.closeNoSaveSc = QShortcut(QKeySequence('Ctrl+W'), self, self.closeNoSave)
        # QKeySequence.PreviousChild(Ctrl+Shift+Backtab) doesn't work
        self.preSc = QShortcut(QKeySequence('Ctrl+Shift+Tab'), self)
        self.nextSc = QShortcut(QKeySequence('Ctrl+Tab'), self)

    def needSave(self):
        return (self.textEditor.document().isModified() or
                self.titleEditor.isModified() or self.timeModified or
                self.tagModified)

    def closeEvent(self, event):
        """Normal close will save diary. For cancel operation, call closeNoSave."""
        settings['Editor']['windowGeo'] = str(self.saveGeometry().toHex())
        self.closed.emit(self.id, self.needSave())
        event.accept()

    def closeNoSave(self):
        settings['Editor']['windowGeo'] = str(self.saveGeometry().toHex())
        self.hide()  # use deleteLater to free, not destroy slot or DeleteOnClose attribute
        self.closed.emit(self.id, False)

    def mousePressEvent(self, event):
        """Handle mouse back/forward button"""
        if event.button() == Qt.XButton1:  # back
            self.preSc.activated.emit()
            event.accept()
        elif event.button() == Qt.XButton2:  # forward
            self.nextSc.activated.emit()
            event.accept()
        else:
            super(Editor, self).mousePressEvent(event)

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
        if settings['Editor'].getboolean('titleFocus'):
            self.titleEditor.setCursorPosition(0)
        else:
            self.textEditor.setFocus()
            self.textEditor.moveCursor(QTextCursor.Start)
        event.accept()
