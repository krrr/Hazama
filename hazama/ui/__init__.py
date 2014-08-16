from PySide.QtGui import QApplication, QIcon, QFont, QFontMetrics, QMessageBox
from PySide.QtCore import QLocale, QTranslator, QLibraryInfo, QDateTime, QFile, QIODevice
from config import settings
from ui import rc
import sys
import os
import time
import logging


def datetimeTrans(s):
    """Convert datetime in database format to locale one"""
    dt = QDateTime.fromString(s, 'yyyy-MM-dd HH:mm')
    return locale.toString(dt, (dateFmt + ' ' + timeFmt) if timeFmt else dateFmt)


def setDatetimeTrans():
    """Set datetime format used in datetimeTrans. Set date format to default
    if it not set."""
    global timeFmt, dateFmt
    timeFmt = settings['Main'].get('timeformat', raw=True)
    dateFmt = settings['Main'].get('dateformat', raw=True)
    if dateFmt is None:
        dateFmt = settings['Main']['dateformat'] = locale.dateFormat()


def currentDatetime():
    """Return current datetime in database format"""
    return time.strftime('%Y-%m-%d %H:%M')


def setTranslationLocale():
    lang = settings['Main'].get('lang', 'en')
    logging.info('Set translation(%s)', lang)
    global trans, transQt  # avoid being collected
    trans = QTranslator()
    trans.load(lang, 'lang/')
    transQt = QTranslator()
    ret = transQt.load('qt_' + lang,
                       QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    if not ret:  # frozen
        transQt.load('qt_'+lang, 'lang/')
    for i in [trans, transQt]: app.installTranslator(i)
    global locale
    sysLocale = QLocale.system()
    # special case: application language is different from system's
    locale = sysLocale if lang == sysLocale.name() else QLocale(lang)


def showDbError(hint=''):
    """If unable to access database, display a error and exit"""
    QMessageBox.critical(
        None,
        app.translate('Errors', 'Unable to access database'),
        app.translate('Errors', 'SQLite3: %s.\n\nIf database path is correct, '
                      'should recover this file by hand or restore from backups.') % hint)


def setStdEditMenuIcons(menu):
    """Add system theme icons to QLineEdit and QTextEdit context-menu"""
    (undo, redo, __, cut, copy, paste, delete, __, sel, *__) = menu.actions()
    undo.setIcon(QIcon.fromTheme('edit-undo'))
    redo.setIcon(QIcon.fromTheme('edit-redo'))
    cut.setIcon(QIcon.fromTheme('edit-cut'))
    copy.setIcon(QIcon.fromTheme('edit-copy'))
    paste.setIcon(QIcon.fromTheme('edit-paste'))
    delete.setIcon(QIcon.fromTheme('edit-delete'))
    sel.setIcon(QIcon.fromTheme('edit-select-all'))


def setStyleSheet():
    if '-stylesheet' in sys.argv:
        logging.info('Override default StyleSheet by command line arg')
    else:
        f = QFile(':/default.qss')
        f.open(QIODevice.ReadOnly | QIODevice.Text)
        ss = str(f.readAll())
        f.close()
        if os.path.isfile('custom.qss'):
            logging.info('Set custom StyleSheet')
            ss += open('custom.qss', encoding='utf-8').read()
        app.setStyleSheet(ss)


class Fonts:
    """Manage all fonts used in application"""
    def __init__(self):
        self.title = QFont()
        self.date = QFont()
        self.text = QFont()
        self.default = app.font()
        self.default_m = QFontMetrics(self.default)
        self.title_m = self.date_m = self.date_m = None

    def load(self):
        self.title.fromString(settings['Font'].get('title'))
        self.title_m = QFontMetrics(self.title)
        self.date.fromString(settings['Font'].get('datetime'))
        self.date_m = QFontMetrics(self.date)
        self.text.fromString(settings['Font'].get('text'))
        if settings['Font'].get('default'):
            self.default.fromString(settings['Font'].get('default'))
            self.default_m = QFontMetrics(self.default)
            app.setFont(self.default)


# setup application icon
app = QApplication(sys.argv)
appIcon = QIcon(':/appicon16.png')
appIcon.addFile(':/appicon32.png')
appIcon.addFile(':/appicon48.png')
appIcon.addFile(':/appicon64.png')
app.setWindowIcon(appIcon)
# setup fonts after qApp created
font = Fonts()
font.load()

setTranslationLocale()
setStyleSheet()
setDatetimeTrans()

