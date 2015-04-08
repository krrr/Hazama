from PySide.QtGui import *
from PySide.QtCore import *
from ui.configdialog_ui import Ui_configDialog
from ui import font, setStyleSheet, readRcTextFile
from config import settings
from hazama import __version__
import db
import logging


languages = {'en': 'English', 'zh_CN': '简体中文', 'ja_JP': '日本語'}
languagesR = {b: a for a, b in languages.items()}
themes = ['1px-rect', 'colorful']


class ConfigDialog(QDialog, Ui_configDialog):
    langChanged = Signal()
    bkRestored = Signal()
    accepted = Signal()

    def __init__(self, parent=None):
        super(ConfigDialog, self).__init__(parent, Qt.WindowTitleHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)
        about = readRcTextFile(':/noicon/about.html').format(
            ver=__version__, author=self.tr('author'),
            checkupdate=self.tr('check-update'))
        self.aboutBrowser.setHtml(about)
        self.aboutBrowser.document().setDocumentMargin(0)
        self.openOutBtn.hide()  # can't set initial state in creator
        # load settings
        self.aindCheck.setChecked(settings['Editor'].getboolean('autoIndent', True))
        self.tListCountCheck.setChecked(settings['Main'].getboolean('tagListCount', True))
        self.tfocusCheck.setChecked(settings['Editor'].getboolean('titleFocus', False))
        self.bkCheck.setChecked(settings['Main'].getboolean('backup', True))
        # language ComboBox
        for l in sorted(languagesR):
            self.langCombo.addItem(l)
        lang = settings['Main'].get('lang', 'en')
        langIndex = self.langCombo.findText(languages.get(lang, 'English'))
        self.langCombo.setCurrentIndex(langIndex)

        self.rstCombo.model().item(0).setSelectable(False)
        self.rstCombo.addItems(db.list_backups())
        self.themeCombo.addItems(themes)
        self.themeCombo.setCurrentIndex(
            themes.index(settings['Main'].get('theme', '1px-rect')))
        self.preLinesBox.setValue(settings['Main'].getint('previewLines', 4))
        # setup font buttons & load settings(fonts)
        self.defFontGBox.setChecked(bool(settings['Font'].get('default')))
        self.dtFontBtn.configName = 'datetime'
        self.titleFontBtn.configName = 'title'
        self.textFontBtn.configName = 'text'
        self.defFontBtn.configName = 'default'
        self.buttons = (self.dtFontBtn, self.titleFontBtn, self.textFontBtn,
                        self.defFontBtn)
        for i in self.buttons:
            i.clicked.connect(self.handleFontBtn)
            self._setFontButton(i, getattr(font, i.configName))

    def showEvent(self, event):
        # set minimum height of aboutBrowser according to its contents
        doc = self.aboutBrowser.document()
        self.aboutBrowser.setMinimumHeight(int(doc.size().height()))

    def accept(self):
        settings['Editor']['autoIndent'] = str(self.aindCheck.isChecked())
        settings['Main']['tagListCount'] = str(self.tListCountCheck.isChecked())
        settings['Editor']['titleFocus'] = str(self.tfocusCheck.isChecked())
        settings['Main']['backup'] = str(self.bkCheck.isChecked())
        settings['Main']['previewLines'] = str(self.preLinesBox.value())
        for i in self.buttons:
            settings['Font'][i.configName] = i.font().toString()
        if not self.defFontGBox.isChecked() and settings['Font']['default']:
            del settings['Font']['default']
        font.load()

        lang = languagesR[self.langCombo.currentText()]
        if settings['Main'].get('lang', 'en') != lang:
            settings['Main']['lang'] = lang
            self.langChanged.emit()

        theme = self.themeCombo.currentText()
        if settings['Main'].get('theme', '1px-rect') != theme:
            settings['Main']['theme'] = theme
            setStyleSheet()

        logging.info('Settings saved')
        self.accepted.emit()
        self.close()

    @Slot()
    def on_exportBtn_clicked(self):
        export_all = self.exportOption.currentIndex() == 0
        nList = self.parent().nList

        path, _type = QFileDialog.getSaveFileName(
            parent=self,
            caption=self.tr('Export Diary'),
            filter=self.tr('Plain Text (*.txt)'))
        if path == '': return    # dialog cancelled
        try:
            nList.handleExport(path, export_all)
        except Exception as e:
            QMessageBox.warning(self, self.tr('Export Failed'), '%-20s' % e)
            return

        if not self.openOutBtn.isVisible():
            self.openOutBtn.show()
        else:  # two or more export happened
            self.openOutBtn.clicked.disconnect()
        self.openOutBtn.setFocus()
        self.openOutBtn.clicked.connect(
            lambda: QDesktopServices.openUrl('file:///' + path))

    @Slot(str)
    def on_rstCombo_activated(self, filename):
        """Restore database backup"""
        ret = QMessageBox.question(
            self, self.tr('Restore backup'),
            self.tr('All diaries will be replaced with that backup!'),
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
        # set sample text in dialog with some hack
        try:
            sample = dlg.findChildren(QLineEdit)[3]
            sample.setText('AaBbYy@2013 %s' % self.langCombo.currentText())
        except Exception:
            pass  # it may fail in the future
        ret = dlg.exec_()
        if ret:
            self._setFontButton(btn, dlg.selectedFont())

    @staticmethod
    def _setFontButton(btn, font_):
        """Set Font Button's text and font"""
        btn.setFont(font_)
        family = font_.family() if font_.exactMatch() else QFontInfo(font_).family()
        btn.setText('%s %spt' % (family, font_.pointSize()))
