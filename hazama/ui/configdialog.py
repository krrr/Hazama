import sys
import logging
from PySide.QtGui import *
from PySide.QtCore import *
from hazama import __version__, diarybook, mactype
from hazama.ui import (font, loadStyleSheet, scaleRatio, fixWidgetSizeOnHiDpi, isDwmUsable,
                       DB_DATETIME_FMT_QT, makeQIcon, setTranslationLocale,
                       TRANS_DISPLAY_NAMES, TRANSLATIONS, THEMES, THEME_COLORFUL_SCHEMES)
from hazama.ui.configdialog_ui import Ui_configDialog
from hazama.config import settings, db, isWin7OrLater, isWin, CUSTOM_STYLESHEET_DELIMIT
from hazama.ui.customobjects import QSSHighlighter
from hazama.ui.customwidgets import FontSelectButton
from hazama import updater


aboutBrowserCss = '''
p, ul {margin:0px; font-size:9pt;}
a {color:#00345e; text-decoration: none;}
'''
aboutInfo = '''
<p align="center">{title}</p>

<p align="center" style="margin-top:4px;">
    <a href="hazama://check-update">{check_update}</a>
    &nbsp;
    <a href="https://krrr.github.io/hazama">{website}</a>
    &nbsp;
    <a href="https://github.com/krrr">{author}</a>
</p>
'''
aboutUpdate = '''
<p align="center">v{curtVer} <b>({title})</b></p>
<p align="center">{size}: 10-15MB</p>

{note}

<p align="center" style="margin-top:4px;">
  <a href="hzm://install-update">{install}</a>
  &nbsp;
  <a href="hzm://ignore-update">{ignore}</a>
</p>
'''
aboutUpdateNoInstall = '''
<p align="center">v{curtVer} <b>({title})</b></p>

{note}

<p align="center" style="margin-top:4px;">
    <a href="https://krrr.github.io/hazama">{website}</a>
    &nbsp;
  <a href="hzm://ignore-update">{ignore}</a>
</p>
'''
aboutError = '''
<p align="center">{title}</p>

<p align="center" style="margin-top:4px;">
  <a href="hzm://{cmd}">{retry}</a>
  &nbsp;
  <a href="hzm://show-info">{ok}</a>
</p>
'''


def _set_check_changed(section, key, value, default=None):
    old = settings[section].get(key, None)
    new = str(value)
    settings[section][key] = new
    return old != new


class ConfigDialog(QDialog, Ui_configDialog):
    diaryChanged = Signal()
    appearanceChanged = Signal()

    def __init__(self, parent):
        super().__init__(parent, Qt.WindowTitleHint)
        self._checkUpdateTask = self._installUpdateTask = None
        self._dlProgressBlocks = None
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)
        fixWidgetSizeOnHiDpi(self)

        # about browser
        self.aboutBrowser.anchorClicked.connect(self._NavigateAboutArea)
        self.aboutBrowser.document().setDocumentMargin(0)
        self.aboutBrowser.document().setDefaultStyleSheet(aboutBrowserCss)
        if updater.foundUpdate:
            self._NavigateAboutArea(QUrl('hzm://show-update'))
        elif updater.checkUpdateTask:
            # signal losing is impossible? because of GIL
            task = self._checkUpdateTask = updater.checkUpdateTask
            task.succeeded.connect(self._onCheckUpdateSucceeded)
            task.failed.connect(self._aboutAreaError)
            self._NavigateAboutArea(QUrl('hzm://show-info/' + self.tr('checking...')))
        else:
            self._NavigateAboutArea(QUrl('hzm://show-info'))

        if scaleRatio > 1:
            self.openOutBtn.setIcon(makeQIcon(':/check.png', scaled2x=True))
        self.openOutBtn.hide()  # can't set initial state in creator
        self.appIcoBtn.setIcon(qApp.windowIcon())
        self.appIcoBtn.setIconSize(QSize(32, 32) * scaleRatio)
        self.appIcoBtn.setStyleSheet('border: none')
        self.appIcoBtn.clicked.connect(self._easterEgg)

        self.updateCheck.setChecked(settings['Update'].getboolean('autoCheck'))
        self.aindCheck.setChecked(settings['Editor'].getboolean('autoIndent'))
        self.tabIndentCheck.setChecked(settings['Editor'].getboolean('tabIndent'))
        self.autoRoCheck.setChecked(settings['Editor'].getboolean('autoReadOnly'))
        self.tListCountCheck.setChecked(settings['Main'].getboolean('tagListCount'))
        self.annotateCheck.setChecked(settings['Main'].getboolean('listAnnotated'))
        if settings['Editor'].getboolean('titleFocus'):
            self.focusTitleRadio.setChecked(True)
        else:
            self.focusTextRadio.setChecked(True)
        self.bkCheck.setChecked(settings['Main'].getboolean('backup'))
        self.extendBgCheck.setChecked(settings['Main'].getboolean('extendTitleBarBg'))
        if isWin and not isDwmUsable():
            self.extendBgCheck.setEnabled(False)
        # language ComboBox
        for i in TRANS_DISPLAY_NAMES:
            self.langCombo.addItem(i)
        langIndex = TRANSLATIONS.index(settings['Main']['lang'])
        self.langCombo.setCurrentIndex(langIndex)

        self.rstCombo.model().item(0).setSelectable(False)
        self.rstCombo.addItems(diarybook.list_backups())
        self.themeCombo.addItems(THEMES)
        self.themeCombo.setCurrentIndex(THEMES.index(settings['Main']['theme']))
        self.preLinesBox.setValue(settings['Main'].getint('previewLines'))
        # theme specific
        if settings['Main']['theme'] == '1px-rect':
            self._disableThemeSpe()
        else:
            self._enableThemeSpe()
        self.themeCombo.currentIndexChanged.connect(
            lambda idx: self._enableThemeSpe() if idx != 0 else self._disableThemeSpe())
        # fonts
        self.enRenderCheck.setChecked(settings['Font'].getboolean('enhanceRender'))
        self.enRenderCheck.setVisible(isWin)
        self.enRenderCheck.setEnabled(mactype.isUsable())
        self.defFontGBox.setChecked('default' in settings['Font'])
        self.fontBtns = (self.dtFontBtn, self.titleFontBtn, self.textFontBtn,
                         self.defFontBtn)
        fontBtnConfigNames = ('datetime', 'title', 'text', 'default')
        fontDialogPreview = 'AaBbYy@2017 %s' % self.langCombo.currentText()

        for b, n in zip(self.fontBtns, fontBtnConfigNames):
            b.configName = n
            b.resettable = n != 'default'
            b.PreviewText = fontDialogPreview  # change class var may cause segfault!
            font_ = getattr(font, n)
            b.setFont(font_, font_.userSet)  # userSet is set by Font in __init__
            if scaleRatio > 1:
                b.setMinimumWidth((b.minimumWidth() * scaleRatio))
        # setup statistics
        diaryCount = len(db)
        if diaryCount < 2:
            diaryDtRange = None
        elif settings['Main']['listSortBy'] == 'datetime' and parent:
            # only save 10 milliseconds (600 diaries)
            m = parent.diaryList.model()
            diaryDtRange = m.data(m.index(0, 1)), m.data(m.index(m.rowCount()-1, 1))
            if settings['Main'].getboolean('listReverse'):
                diaryDtRange = diaryDtRange[::-1]
        else:
            diaryDtRange = db.get_datetime_range()
        if diaryDtRange:
            qRange = tuple(map(lambda x: QDateTime.fromString(x, DB_DATETIME_FMT_QT),
                               diaryDtRange))
            days = qRange[0].daysTo(qRange[1])
        else:
            days = 0
        if days > 0:
            freq = round(1 / (diaryCount / days), 1)
            oldest, newest = map(lambda x: x[:7], diaryDtRange)
            self.staLabel.setText(self.tr('Every <b>%s</b> days a diary, from <b>%s</b> to <b>%s</b>') %
                                  (freq, oldest, newest))
        else:
            self.staLabel.setText(self.tr('N/A'))

    def showEvent(self, event):
        super().showEvent(event)  # centered on parent window
        # call to adjust has no effect before showing
        self._adjustAboutAreaHeight()

    def reject(self):
        self._cleanUp()
        super().reject()

    def accept(self):
        """Save settings here."""
        # these settings may trigger signals
        langChanged = _set_check_changed('Main', 'lang', TRANSLATIONS[self.langCombo.currentIndex()])
        lookChanged = False
        lookChanged |= _set_check_changed('Main', 'theme', self.themeCombo.currentText())
        lookChanged |= _set_check_changed('Main', 'extendTitleBarBg', self.extendBgCheck.isChecked())
        lookChanged |= _set_check_changed('Main', 'listAnnotated', self.annotateCheck.isChecked())
        lookChanged |= _set_check_changed('Main', 'previewLines', self.preLinesBox.value())

        settings['Update']['autoCheck'] = str(self.updateCheck.isChecked())
        settings['Editor']['autoIndent'] = str(self.aindCheck.isChecked())
        settings['Editor']['tabIndent'] = str(self.tabIndentCheck.isChecked())
        settings['Editor']['autoReadOnly'] = str(self.autoRoCheck.isChecked())
        settings['Main']['tagListCount'] = str(self.tListCountCheck.isChecked())
        settings['Editor']['titleFocus'] = str(self.focusTitleRadio.isChecked())
        settings['Main']['backup'] = str(self.bkCheck.isChecked())
        settings['Font']['enhanceRender'] = str(self.enRenderCheck.isChecked())

        oldFonts = tuple(sorted(settings['Font'].items()))
        for b in self.fontBtns:
            settings['Font'][b.configName] = b.font().toString() if b.userSet else ''
        if not self.defFontGBox.isChecked() and 'default' in settings['Font']:
            del settings['Font']['default']
        fontsChanged = oldFonts != tuple(sorted(settings['Font'].items()))

        schemeChanged = False
        scheme = self.schemeCombo.currentText()
        if self.themeCombo.currentText() == 'colorful':
            schemeChanged = scheme != settings['ThemeColorful']['colorScheme']
            settings['ThemeColorful']['colorScheme'] = scheme

        # be careful about the order of following operations
        if langChanged:
            setTranslationLocale()
            fontsChanged = True  # maybe
        if fontsChanged:
            font.load()
        if fontsChanged or schemeChanged or lookChanged:
            # Load style sheet first because many size calculation rely on it.
            # But some style sheet used dynamic properties, manual refresh is needed.
            loadStyleSheet()
            self.appearanceChanged.emit()

        logging.info('settings saved')
        self._cleanUp()
        super().accept()
        self.close()

    def _cleanUp(self):
        if self._checkUpdateTask:
            self._checkUpdateTask.disConn()
        if self._installUpdateTask:
            self._installUpdateTask.canceled = True
            self._installUpdateTask.disConn()

    def _disableThemeSpe(self):
        for i in [self.schemeCombo, self.schemeLabel]:
            i.setDisabled(True)
        self.schemeCombo.clear()

    def _enableThemeSpe(self):
        theme = self.themeCombo.currentText()
        for i in [self.schemeCombo, self.schemeLabel]:
            i.setEnabled(True)
        if theme == 'colorful':
            self.schemeCombo.addItems(THEME_COLORFUL_SCHEMES)
            scm = settings['ThemeColorful']['colorScheme']
            self.schemeCombo.setCurrentIndex(THEME_COLORFUL_SCHEMES.index(scm))

    def _easterEgg(self):
        if self.appIcoBtn.icon().isNull():
            return

        def flyPaperPlane():
            nonlocal v
            v += 0.3
            flyIco.move(flyIco.pos() - QPoint(v, v))
            if flyIco.x() < -100:
                timer.stop()

        flyIco = QLabel(self)
        flyIco.setPixmap(self.appIcoBtn.icon().pixmap(self.appIcoBtn.iconSize()))
        flyIco.setAlignment(Qt.AlignCenter)
        flyIco.setFixedSize(self.appIcoBtn.size())
        pos = self.appIcoBtn.mapTo(self, QPoint(0, 0))
        flyIco.move(pos)
        flyIco.show()
        self.appIcoBtn.setFixedSize(self.appIcoBtn.size())
        self.appIcoBtn.setIcon(QIcon())  # set empty icon to hold place
        v = 1.0
        timer = QTimer(self.appIcoBtn)
        timer.timeout.connect(flyPaperPlane)
        timer.start(16)

        def textEater():
            nonlocal count
            if not count:
                return timer2.stop()
            t = self.infoBox.title()
            self.infoBox.setTitle(t[:idx] + t[idx+1:])
            count -= 1
            timer2.start(timer2.interval() - 15)

        idx = self.infoBox.title().index('H')
        count = 6
        timer2 = QTimer(self.appIcoBtn)
        timer2.timeout.connect(textEater)
        timer2.start(100)

    def _adjustAboutAreaHeight(self):
        doc = self.aboutBrowser.document()
        self.aboutBrowser.setMinimumHeight(int(doc.size().height()))

    def _NavigateAboutArea(self, url):
        if url.isLocalFile() or url.scheme().startswith('http'):
            return QDesktopServices.openUrl(url)

        cmd = url.host()
        if cmd == 'show-info':
            title = 'v'+__version__
            if url.path():
                title += ' <b>(' + url.path()[1:] + ')</b>'
            about = aboutInfo.format(
                title=title, author=self.tr('Author'), website=self.tr('Website'),
                check_update=self.tr('Check update'))
            self.aboutBrowser.setHtml(about)
            self._adjustAboutAreaHeight()
        if cmd == 'check-update':
            if self._checkUpdateTask and self._checkUpdateTask.isRunning():
                return
            if self._checkUpdateTask:
                self._checkUpdateTask.disConn()
            task = self._checkUpdateTask = updater.CheckUpdate()
            task.succeeded.connect(self._onCheckUpdateSucceeded)
            task.failed.connect(self._aboutAreaError)
            task.start()
            self._setAboutArea(self.tr('checking...'), False)
        elif cmd == 'show-update':  # triggered by check-update
            update = updater.foundUpdate
            if update is None:
                return self._NavigateAboutArea(QUrl('hzm://show-info/' + self.tr('up-to-date')))

            common = {'ignore': self.tr('Ignore this version'), 'curtVer': __version__,
                      'title': self.tr('New version: v%s') % update.version,
                      'note': update.note_html}
            if hasattr(sys, 'frozen') and isWin7OrLater:
                self.aboutBrowser.setHtml(aboutUpdate.format(
                    install=self.tr('Install'), size=self.tr('Size'), **common))
                self._adjustAboutAreaHeight()
            else:
                self.aboutBrowser.setHtml(aboutUpdateNoInstall.format(
                    website=self.tr('Website'), **common))
                self._adjustAboutAreaHeight()
        elif cmd == 'install-update':
            self._setAboutArea(self.tr('Connecting...'))
            self._dlProgressBlocks = max(
                int(self.aboutBrowser.width() * 0.8 / font.default_m.width('▇')), 8)
            task = self._installUpdateTask = updater.InstallUpdate(updater.foundUpdate)
            task.progress.connect(self._onInstallUpdateProgress)
            task.downloadFinished.connect(self._onDownloadFinished)
            task.succeeded.connect(self._onInstallUpdateSucceeded)
            task.failed.connect(self._aboutAreaError)
            task.start()
        elif cmd == 'ignore-update':
            settings['Update']['newestIgnoredVer'] = updater.foundUpdate.version
            self._NavigateAboutArea(QUrl('hzm://show-info'))
            updater.foundUpdate = None
            self.parent().setUpdateHint(False)

    def _aboutAreaError(self, msg):
        if self.sender() == self._checkUpdateTask:
            err = self.tr('Failed to check update: %s')
            cmd = 'check-update'
        else:
            err = self.tr('Failed to install update: %s')
            cmd = 'install-update'
        self.aboutBrowser.setHtml(aboutError.format(
            title=err % msg, retry=self.tr('Retry'), cmd=cmd, ok=self.tr('OK')))
        self._adjustAboutAreaHeight()

    def _setAboutArea(self, oneLine, adjust=True):
        self.aboutBrowser.setHtml('<p align="center">%s</p>' % oneLine)
        if adjust:
            self._adjustAboutAreaHeight()

    @Slot()
    def on_exportBtn_clicked(self):
        export_all = self.exportOption.currentIndex() == 0

        path, _type = QFileDialog.getSaveFileName(
            parent=self,
            caption=self.tr('Export Diary'),
            filter=self.tr('Plain Text (*.txt)'))
        if path == '': return    # dialog cancelled
        try:
            self.parent().diaryList.handleExport(path, export_all)
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
        msg = QMessageBox(self)
        okBtn = msg.addButton(qApp.translate('Dialog', 'Restore'), QMessageBox.AcceptRole)
        msg.setIcon(QMessageBox.Question)
        msg.addButton(qApp.translate('Dialog', 'Cancel'), QMessageBox.RejectRole)
        msg.setWindowTitle(self.tr('Restore backup'))
        msg.setText(self.tr('Current diary book will be replaced with the backup!'))
        msg.exec_()
        msg.deleteLater()

        if msg.clickedButton() == okBtn:
            diarybook.restore_backup(filename)
            self.close()
            self.diaryChanged.emit()
        else:
            self.rstCombo.setCurrentIndex(0)

    def _onCheckUpdateSucceeded(self):
        self._NavigateAboutArea(QUrl('hzm://show-update'))

    def _onInstallUpdateSucceeded(self):
        self._setAboutArea(self.tr('Succeeded (Restart needed for update to take effect)'))
        updater.foundUpdate = None
        self.parent().setUpdateHint(False)

    def _onInstallUpdateProgress(self, received, total):
        self._setAboutArea(updater.textProgressBar(
            received, total, barLen=self._dlProgressBlocks), False)

    def _onDownloadFinished(self):
        self._setAboutArea(self.tr('Installing...'))


class StyleSheetEditor(QDialog):
    appearanceChanged = Signal()

    def __init__(self, parent):
        super().__init__(parent, Qt.WindowTitleHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle('Style Sheet Editor')

        self._buttonBox = QDialogButtonBox(self)
        self._applyBtn = self._buttonBox.addButton('Apply (till restart)',
                                                   QDialogButtonBox.ApplyRole)
        self._saveBtn = self._buttonBox.addButton('Save', QDialogButtonBox.AcceptRole)
        self._cancelBtn = self._buttonBox.addButton('Cancel', QDialogButtonBox.RejectRole)
        self._buttonBox.clicked.connect(self.onButtonBoxClicked)

        codeFont = QFont('Consolas' if isWin else 'monospace')
        self.styleSheetEdit = QPlainTextEdit(self)
        self.styleSheetEdit.setFont(codeFont)
        self.styleSheetEdit.setStyleSheet('''
        QPlainTextEdit { border: none; }
        ''')
        self._highlighter = QSSHighlighter(self.styleSheetEdit.document())
        self.styleSheetEdit.setPlainText(qApp.originStyleSheet)
        layout = QVBoxLayout(self)
        layout.addWidget(self.styleSheetEdit)
        layout.addWidget(self._buttonBox)

    def onButtonBoxClicked(self, btn):
        if btn == self._cancelBtn:
            return self.close()

        qApp.setStyleSheet(self.styleSheetEdit.toPlainText())
        if btn == self._saveBtn:
            ss = self.styleSheetEdit.toPlainText().partition(CUSTOM_STYLESHEET_DELIMIT)[2]
            with open('custom.qss', 'w', encoding='utf-8') as f:
                f.write(ss)
            self.close()

        self.appearanceChanged.emit()
