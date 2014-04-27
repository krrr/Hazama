from PySide.QtGui import *
from PySide.QtCore import *
from .configdialog_ui import Ui_Settings
from . import font
from config import settings
import db
import logging


class ConfigDialog(QDialog, Ui_Settings):
    langChanged = Signal()
    needExport = Signal(bool)  # arg: export_all
    bkRestored = Signal()
    accepted = Signal()
    lang2index = {'en': 0, 'zh_CN': 1, 'ja': 2}  # index used in lang combo
    index2lang = {b: a for (a, b) in lang2index.items()}

    def __init__(self, parent=None):
        super(ConfigDialog, self).__init__(parent, Qt.WindowTitleHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.setFont(font.sys)
        # load settings
        self.aindCheck.setChecked(settings['Editor'].getint('autoindent', 1))
        self.tfocusCheck.setChecked(settings['Editor'].getint('titlefocus', 0))
        self.bkCheck.setChecked(settings['Main'].getint('backup', 1))
        self.langCombo.setCurrentIndex(self.lang2index[
                                       settings['Main'].get('lang', 'en')])
        self.rstCombo.model().item(0).setSelectable(False)
        self.rstCombo.addItems(db.list_backups())
        self.preLinesBox.setValue(settings['Main'].getint('previewlines', 4))
        # load settings(fonts)
        self.defFontGBox.setChecked(bool(settings['Font'].get('default')))
        self.dtFontBtn.configName = 'datetime'
        self.titleFontBtn.configName = 'title'
        self.textFontBtn.configName = 'text'
        self.defFontBtn.configName = 'default'
        self.buttons = [self.dtFontBtn, self.titleFontBtn, self.textFontBtn,
                        self.defFontBtn]
        for i in self.buttons:
            i.clicked.connect(self.handleFontBtn)
            # parm font.data in getattr is for dtFontBtn
            self.setFontButton(i, getattr(font, i.configName, font.date))

    def accept(self):
        settings['Editor']['autoindent'] = str(self.aindCheck.isChecked().real)
        settings['Editor']['titlefocus'] = str(self.tfocusCheck.isChecked().real)
        settings['Main']['backup'] = str(self.bkCheck.isChecked().real)
        settings['Main']['previewlines'] = str(self.preLinesBox.value())
        for i in self.buttons:
            settings['Font'][i.configName] = i.font().toString()
        if not self.defFontGBox.isChecked() and settings['Font']['default']:
            del settings['Font']['default']
        lang = self.index2lang[self.langCombo.currentIndex()]
        if settings['Main'].get('lang', 'en') != lang:
            settings['Main']['lang'] = lang
            self.langChanged.emit()
        logging.info('Settings saved')
        font.load()
        self.accepted.emit()
        self.close()

    @Slot()
    def on_exportBtn_clicked(self):
        export_all = not bool(self.exportOption.currentIndex())
        self.needExport.emit(export_all)

    @Slot(str)
    def on_rstCombo_activated(self, filename):
        """Restore database backup"""
        ret = QMessageBox.question(self, self.tr('Restore backup'),
                                   self.tr('All diaries in book will be '
                                           'lost.Do it?'),
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.No: return
        db.restore_backup(filename)
        self.rstCombo.setCurrentIndex(0)
        self.bkRestored.emit()

    def handleFontBtn(self):
        btn = self.sender()
        f, ok = QFontDialog.getFont(btn.font(), self)
        if ok:
            self.setFontButton(btn, f)

    @staticmethod
    def setFontButton(btn, _font):
        """Set Font Button's text and text's font according to parm. _font"""
        p = lambda f: '%s %spt' % (f.family(), f.pointSize())
        btn.setFont(_font)
        btn.setText(p(_font))
