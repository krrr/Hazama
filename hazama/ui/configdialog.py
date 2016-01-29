import logging
from PySide.QtGui import *
from PySide.QtCore import *
from hazama import __version__, db
from hazama.ui import (font, setStyleSheet, readRcTextFile, isDwmUsable, getDpiScaleRatio,
                       fixWidgetSizeOnHiDpi)
from hazama.ui.configdialog_ui import Ui_configDialog
from hazama.config import settings, nikki


languages = {'en': 'English', 'zh_CN': '简体中文', 'ja_JP': '日本語'}
languagesR = {b: a for a, b in languages.items()}
themes = ['1px-rect', 'colorful']
colorfulSchemes = ['green', 'yellow', 'white']


class ConfigDialog(QDialog, Ui_configDialog):
    langChanged = Signal()
    bkRestored = Signal()
    accepted = Signal()
    extendBgChanged = Signal()

    def __init__(self, parent=None, diaryDtRange=None):
        super(ConfigDialog, self).__init__(parent, Qt.WindowTitleHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)
        fixWidgetSizeOnHiDpi(self)
        about = readRcTextFile(':/about.html').format(
            ver=__version__, author=self.tr('author'),
            checkupdate=self.tr('check-update'))
        self.aboutBrowser.setHtml(about)
        self.aboutBrowser.document().setDocumentMargin(0)
        self.openOutBtn.hide()  # can't set initial state in creator
        self.appIcoLabel.setPixmap(qApp.windowIcon().pixmap(QSize(32, 32) * getDpiScaleRatio()))
        # load settings
        self.aindCheck.setChecked(settings['Editor'].getboolean('autoIndent'))
        self.tListCountCheck.setChecked(settings['Main'].getboolean('tagListCount'))
        if settings['Editor'].getboolean('titleFocus'):
            self.focusTitleRadio.setChecked(True)
        else:
            self.focusTextRadio.setChecked(True)
        self.bkCheck.setChecked(settings['Main'].getboolean('backup'))
        if isDwmUsable():
            self.extendBgCheck.setChecked(
                settings['Main'].getboolean('extendTitleBarBg'))
        else:
            self.extendBgCheck.setDisabled(True)
        # language ComboBox
        for l in sorted(languagesR):
            self.langCombo.addItem(l)
        lang = settings['Main'].get('lang', 'en')
        langIndex = self.langCombo.findText(languages.get(lang, 'English'))
        self.langCombo.setCurrentIndex(langIndex)

        self.rstCombo.model().item(0).setSelectable(False)
        self.rstCombo.addItems(db.list_backups())
        self.themeCombo.addItems(themes)
        self.themeCombo.setCurrentIndex(themes.index(settings['Main']['theme']))
        self.preLinesBox.setValue(settings['Main'].getint('previewLines'))
        # theme specific
        if settings['Main']['theme'] == '1px-rect':
            self._disableThemeSpe()
        else:
            self._enableThemeSpe()
        self.themeCombo.currentIndexChanged.connect(
            lambda idx: self._enableThemeSpe() if idx != 0 else self._disableThemeSpe())
        # setup font buttons & load settings(fonts)
        self.defFontGBox.setChecked('default' in settings['Font'])
        self.dtFontBtn.configName = 'datetime'
        self.titleFontBtn.configName = 'title'
        self.textFontBtn.configName = 'text'
        self.defFontBtn.configName = 'default'
        self.buttons = (self.dtFontBtn, self.titleFontBtn, self.textFontBtn,
                        self.defFontBtn)
        ratio = getDpiScaleRatio()
        for i in self.buttons:
            i.clicked.connect(self._handleFontBtn)
            self._setFontButton(i, getattr(font, i.configName))
            if ratio > 1:
                i.setMinimumWidth((i.minimumWidth() * ratio))
        # setup statistics
        if not diaryDtRange:
            diaryDtRange = nikki.get_datetime_range()
        diaryQtDateRange = tuple(map(lambda x: QDateTime.fromString(x, 'yyyy-MM-dd HH:mm'),
                                     diaryDtRange))
        days = diaryQtDateRange[0].daysTo(diaryQtDateRange[1])
        freq = round(1 / (len(nikki) / days), 1)
        oldest, newest = map(lambda x: x[:7], diaryDtRange)
        self.staLabel.setText(self.tr('Every <b>%s</b> days a diary, from <b>%s</b> to <b>%s</b>') %
                              (freq, oldest, newest))

    def showEvent(self, event):
        # set minimum height of aboutBrowser according to its contents
        doc = self.aboutBrowser.document()
        self.aboutBrowser.setMinimumHeight(int(doc.size().height()))

    def accept(self):
        # special pairs that need trigger signal or call functions
        lang = languagesR[self.langCombo.currentText()]
        langChanged = lang != settings['Main'].get('lang', 'en')
        theme = self.themeCombo.currentText()
        themeChanged = theme != settings['Main']['theme']
        extend = self.extendBgCheck.isChecked()
        extendChanged = extend != settings['Main'].getboolean('extendTitleBarBg')

        settings['Main']['lang'] = lang
        settings['Main']['theme'] = theme
        settings['Main']['extendTitleBarBg'] = str(extend)
        settings['Editor']['autoIndent'] = str(self.aindCheck.isChecked())
        settings['Main']['tagListCount'] = str(self.tListCountCheck.isChecked())
        settings['Editor']['titleFocus'] = str(self.focusTitleRadio.isChecked())
        settings['Main']['backup'] = str(self.bkCheck.isChecked())
        settings['Main']['previewLines'] = str(self.preLinesBox.value())
        for i in self.buttons:
            settings['Font'][i.configName] = i.font().toString()

        schemeChanged = False
        scheme = self.schemeCombo.currentText()
        if theme == 'colorful':
            schemeChanged = scheme != settings['ThemeColorful']['colorScheme']
            settings['ThemeColorful']['colorScheme'] = scheme

        if not self.defFontGBox.isChecked() and 'default' in settings['Font']:
            del settings['Font']['default']
        font.load()

        if langChanged:
            self.langChanged.emit()
        if extendChanged:
            # this change dynamic property, so emit it before setStyleSheet
            self.extendBgChanged.emit()
        if themeChanged or schemeChanged or extendChanged:
            setStyleSheet()

        logging.info('settings changed')
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
        msg = QMessageBox()
        okBtn = msg.addButton(qApp.translate('Dialog', 'Restore'), QMessageBox.AcceptRole)
        msg.setIcon(QMessageBox.Question)
        msg.addButton(qApp.translate('Dialog', 'Cancel'), QMessageBox.RejectRole)
        msg.setWindowTitle(self.tr('Restore backup'))
        msg.setText(self.tr('Current diary book will be replaced with the backup!'))
        msg.exec_()

        if msg.clickedButton() == okBtn:
            db.restore_backup(filename)
            self.close()
            self.bkRestored.emit()
        else:
            self.rstCombo.setCurrentIndex(0)

    def _disableThemeSpe(self):
        for i in [self.schemeCombo, self.schemeLabel]:
            i.setDisabled(True)
        self.schemeCombo.clear()

    def _enableThemeSpe(self):
        theme = self.themeCombo.currentText()
        for i in [self.schemeCombo, self.schemeLabel]:
            i.setEnabled(True)
        if theme == 'colorful':
            self.schemeCombo.addItems(colorfulSchemes)
            scm = settings['ThemeColorful']['colorScheme']
            self.schemeCombo.setCurrentIndex(colorfulSchemes.index(scm))

    def _handleFontBtn(self):
        btn = self.sender()
        dlg = QFontDialog(self)
        dlg.setCurrentFont(btn.font())
        fixWidgetSizeOnHiDpi(dlg)
        # set sample text in dialog with some hack
        try:
            sample = dlg.findChildren(QLineEdit)[3]
            sample.setText('AaBbYy@2013 %s' % self.langCombo.currentText())
        except Exception as e:
            logging.warning('failed to hack Qt font dialog: %s' % e)
        ret = dlg.exec_()
        if ret:
            self._setFontButton(btn, dlg.selectedFont())

    @staticmethod
    def _setFontButton(btn, font_):
        """Set Font Button's text and font"""
        btn.setFont(font_)
        family = font_.family() if font_.exactMatch() else QFontInfo(font_).family()
        btn.setText('%s %spt' % (family, font_.pointSize()))
