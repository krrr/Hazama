from PySide.QtGui import *
from PySide.QtCore import *
from hazama.ui.editor_ui import Ui_editor
from hazama.ui.customobjects import TagCompleter
from hazama.ui.customwidgets import DateTimeDialog
from hazama.ui import font, datetimeTrans, currentDatetime, fullDatetimeFmt, fixWidgetSizeOnHiDpi
from hazama.config import settings, nikki


class Editor(QWidget, Ui_editor):
    """The widget that used to edit diary's body, title, tag and datetime.
    Signal closed: (id of nikki, needSave)
    """
    closed = Signal(int, bool)

    def __init__(self, *args, **kwargs):
        dic = kwargs.pop('nikkiDict')
        super(Editor, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.datetime = self.id = self.timeModified = self.tagModified = None
        geo = settings['Editor'].get('windowGeo')
        if geo:
            self.restoreGeometry(QByteArray.fromHex(geo))
        else:
            fixWidgetSizeOnHiDpi(self)

        self.titleEditor.setFont(font.title)
        self.titleEditor.returnPressed.connect(lambda: self.textEditor.setFocus())
        self.textEditor.setFont(font.text)
        self.textEditor.setAutoIndent(
            settings['Editor'].getboolean('autoIndent'))

        self.dtLabel.setFont(font.datetime)
        sz = max(font.datetime_m.ascent(), 12)
        self.dtBtn.setIconSize(QSize(sz, sz))

        self.tagEditor.setTextMargins(QMargins(2, 0, 2, 0))
        self.tagEditor.setCompleter(
            TagCompleter(list(nikki.gettags()), self.tagEditor))
        saveBtn = self.box.button(QDialogButtonBox.Save)
        self.tagEditor.returnPressed.connect(lambda: saveBtn.setFocus())

        # setup shortcuts
        # seems PySide has problem with QKeySequence.StandardKeys
        self.closeSaveSc = QShortcut(QKeySequence.Save, self, self.close)
        self.closeNoSaveSc = QShortcut(QKeySequence('Ctrl+W'), self, self.closeNoSave)
        # Ctrl+Shift+Backtab doesn't work
        self.preSc = QShortcut(QKeySequence('Ctrl+Shift+Tab'), self)
        self.nextSc = QShortcut(QKeySequence('Ctrl+Tab'), self)

        self.fromNikkiDict(dic)

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
        newDt = DateTimeDialog.getDateTime(dt, fullDatetimeFmt, self)
        if newDt is not None:
            newDtStr = newDt.toString(dbDatetimeFmt)
            if newDtStr != self.datetime:
                self.datetime = newDtStr
                self.dtLabel.setText(datetimeTrans(newDtStr))
                self.timeModified = True

    def fromNikkiDict(self, dic):
        self.timeModified = self.tagModified = False
        self.id = dic['id']
        self.datetime = dic.get('datetime')

        self.dtLabel.setText(datetimeTrans(self.datetime) if self.datetime else '')
        self.titleEditor.setText(dic.get('title', ''))
        self.tagEditor.setText(dic.get('tags', ''))
        self.textEditor.setRichText(dic.get('text', ''), dic.get('formats'))
        # if title is empty, use datetime instead. if no datetime (new), use "New Diary"
        hint = (dic.get('title') or
                (datetimeTrans(self.datetime, stripTime=True) if 'datetime' in dic else None) or
                self.tr('New Diary'))
        self.setWindowTitle("%s - Hazama" % hint)

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
