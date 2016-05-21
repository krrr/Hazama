from PySide.QtGui import *
from PySide.QtCore import *
from hazama.ui.editor_ui import Ui_editor
from hazama.ui.customobjects import TagCompleter
from hazama.ui.customwidgets import DateTimeDialog
from hazama.ui import (font, datetimeTrans, currentDatetime, fullDatetimeFmt,
                       saveWidgetGeo, restoreWidgetGeo, datetimeToQt, dbDatetimeFmtQt)
from hazama.config import settings, nikki


class Editor(QWidget, Ui_editor):
    """The widget that used to edit diary's body, title, tag and datetime.
    Signal closed: (id of nikki, needSave)
    """
    closed = Signal(int, bool)

    def __init__(self, nikkiDict, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.readOnly = self.datetime = self.id = self.timeModified = self.tagModified = None
        restoreWidgetGeo(self, settings['Editor'].get('windowGeo'))

        self.titleEditor.setFont(font.title)
        self.titleEditor.returnPressed.connect(lambda: self.textEditor.setFocus())
        self.textEditor.setFont(font.text)
        self.textEditor.setAutoIndent(settings['Editor'].getboolean('autoIndent'))

        self.dtBtn.setFont(font.datetime)
        sz = max(font.datetime_m.ascent(), 12)
        self.dtBtn.setIconSize(QSize(sz, sz))
        self.lockBtn.setIconSize(QSize(sz, sz))
        self.lockBtn.clicked.connect(lambda: self.setReadOnly(False))

        self.tagEditor.setTextMargins(QMargins(2, 0, 2, 0))
        self.tagEditor.setCompleter(
            TagCompleter(list(nikki.gettags()), self.tagEditor))
        saveBtn = self.box.button(QDialogButtonBox.Save)
        self.tagEditor.returnPressed.connect(lambda: saveBtn.setFocus())

        # setup shortcuts
        # seems PySide has problem with QKeySequence.StandardKeys
        self.closeSaveSc = QShortcut(QKeySequence.Save, self, self.close)
        self.closeNoSaveSc = QShortcut(QKeySequence('Ctrl+W'), self, self.closeNoSave)
        self.quickCloseSc = QShortcut(QKeySequence('Esc'), self, self.closeNoSave)
        # Ctrl+Shift+Backtab doesn't work
        self.preSc = QShortcut(QKeySequence('Ctrl+Shift+Tab'), self)
        self.nextSc = QShortcut(QKeySequence('Ctrl+Tab'), self)

        self.fromNikkiDict(nikkiDict)

    def needSave(self):
        return (self.textEditor.document().isModified() or
                self.titleEditor.isModified() or self.timeModified or
                self.tagModified)

    def closeEvent(self, event):
        """Normal close will save diary. For cancel operation, call closeNoSave."""
        settings['Editor']['windowGeo'] = saveWidgetGeo(self)
        self.closed.emit(self.id, self.needSave())
        event.accept()

    def closeNoSave(self):
        settings['Editor']['windowGeo'] = saveWidgetGeo(self)
        self.hide()  # avoid closeEvent
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
            super().mousePressEvent(event)

    @Slot()
    def on_tagEditor_textEdited(self):
        # tagEditor.isModified() will be reset by completer. So this instead.
        self.tagModified = True

    @Slot()
    def on_dtBtn_clicked(self):
        """Show datetime edit dialog"""
        if self.readOnly: return
        dtStr = currentDatetime() if self.datetime is None else self.datetime
        newDt = DateTimeDialog.getDateTime(datetimeToQt(dtStr), fullDatetimeFmt, self)
        if newDt is not None:
            newDtStr = newDt.toString(dbDatetimeFmtQt)
            if newDtStr != self.datetime:
                self.datetime = newDtStr
                self.dtBtn.setText(datetimeTrans(newDtStr))
                self.timeModified = True

    def setReadOnly(self, readOnly):
        self.titleEditor.setReadOnly(readOnly)
        self.textEditor.setReadOnly(readOnly)
        self.tagEditor.setReadOnly(readOnly)
        self.textEditor.fmtMenu.setEnabled(False)
        self.dtBtn.setCursor(Qt.ArrowCursor if readOnly else Qt.PointingHandCursor)
        self.box.setStandardButtons(QDialogButtonBox.Close if readOnly else
                                    QDialogButtonBox.Cancel | QDialogButtonBox.Save)
        self.lockBtn.setVisible(readOnly)
        self.titleEditor.setVisible(not readOnly or bool(self.titleEditor.text()))
        self.tagEditor.setVisible(not readOnly or bool(self.tagEditor.text()))
        self.quickCloseSc.setEnabled(readOnly)
        self.readOnly = readOnly

    def fromNikkiDict(self, dic):
        self.timeModified = self.tagModified = False
        self.id = dic['id']
        self.datetime = dic.get('datetime')

        self.dtBtn.setText(datetimeTrans(self.datetime) if self.datetime else '')
        self.titleEditor.setText(dic.get('title', ''))
        self.tagEditor.setText(dic.get('tags', ''))
        self.textEditor.setRichText(dic.get('text', ''), dic.get('formats'))
        # if title is empty, use datetime instead. if no datetime (new), use "New Diary"
        t = (dic.get('title') or
             (datetimeTrans(self.datetime, stripTime=True) if 'datetime' in dic else None) or
             self.tr('New Diary'))
        self.setWindowTitle("%s - Hazama" % t)

        readOnly = (settings['Editor'].getboolean('autoReadOnly') and
                    self.datetime is not None and
                    datetimeToQt(self.datetime).daysTo(QDateTime.currentDateTime()) > 3)
        self.setReadOnly(readOnly)

    def toNikkiDict(self):
        text, formats = self.textEditor.getRichText()
        return dict(id=self.id, datetime=self.datetime or currentDatetime(),
                    text=text, formats=formats, title=self.titleEditor.text(),
                    tags=self.tagEditor.text())

    def showEvent(self, event):
        if settings['Editor'].getboolean('titleFocus'):
            self.titleEditor.setCursorPosition(0)
        else:
            self.textEditor.setFocus()
            self.textEditor.moveCursor(QTextCursor.Start)
        event.accept()
