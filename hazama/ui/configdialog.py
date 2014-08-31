from PySide.QtGui import *
from PySide.QtCore import *
from ui.configdialog_ui import Ui_configDialog
from ui import font
from config import settings
import db
import logging


languages = {'en': 'English', 'zh_CN': '简体中文', 'ja_JP': '日本語'}
languagesR = {b: a for a, b in languages.items()}


class ConfigDialog(QDialog, Ui_configDialog):
    langChanged = Signal()
    needExport = Signal(bool)  # arg: export_all
    bkRestored = Signal()
    accepted = Signal()

    def __init__(self, parent=None):
        super(ConfigDialog, self).__init__(parent, Qt.WindowTitleHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)
        # load settings
        self.aindCheck.setChecked(settings['Editor'].getint('autoindent', 1))
        self.tfocusCheck.setChecked(settings['Editor'].getint('titlefocus', 0))
        self.bkCheck.setChecked(settings['Main'].getint('backup', 1))
        # load settings(language ComboBox)
        for l in sorted(languagesR):
            self.langCombo.addItem(l)
        lang = settings['Main'].get('lang', 'en')
        langIndex = self.langCombo.findText(languages.get(lang, 'English'))
        self.langCombo.setCurrentIndex(langIndex)
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
        font.load()
        lang = languagesR[self.langCombo.currentText()]
        if settings['Main'].get('lang', 'en') != lang:
            settings['Main']['lang'] = lang
            self.langChanged.emit()
        logging.info('Settings saved')
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
        if ret == QMessageBox.Yes:
            db.restore_backup(filename)
            self.bkRestored.emit()
            self.close()
        else:
            self.rstCombo.setCurrentIndex(0)

    def handleFontBtn(self):
        btn = self.sender()
        dlg = QFontDialog(self)
        dlg.setCurrentFont(btn.font())
        # Set sample text in dialog with some hack
        try:
            sample = dlg.findChildren(QLineEdit)[3]
            sample.setText('AaBbYy 2013 %s' % self.langCombo.currentText())
        except (IndexError, AttributeError):
            pass
        ret = dlg.exec_()
        if ret:
            self.setFontButton(btn, dlg.selectedFont())

    @staticmethod
    def setFontButton(btn, f):
        """Set Font Button's text and font"""
        btn.setFont(f)
        btn.setText('%s %spt' % (f.family(), f.pointSize()))

