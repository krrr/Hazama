from PySide.QtGui import QApplication, QIcon, QFont, QFontMetrics, QMessageBox
from PySide.QtCore import QLocale, QTranslator, QLibraryInfo, QDateTime
from config import settings
from ui import rc
import sys
import os
import time
import logging



def datetimeTrans(s):
    """Convert datetime in database format to locale one"""
    dt = QDateTime.fromString(s, 'yyyy-MM-dd HH:mm')
    return (locale.toString(dt, date_fmt + ' ' + time_fmt) if time_fmt
            else locale.toString(dt, date_fmt))


def setDatetimeTrans():
    """Set datetime format used in datetimeTrans. Set date format to default
    if it not set."""
    global time_fmt, date_fmt
    time_fmt = settings['Main'].get('timeformat', raw=True)
    date_fmt = settings['Main'].get('dateformat', raw=True)
    if date_fmt is None:
        sys_date_fmt = locale.dateFormat()
        settings['Main']['dateformat'] = sys_date_fmt
        date_fmt = sys_date_fmt


def currentDatetime():
    """Return current datetime in database format"""
    return time.strftime('%Y-%m-%d %H:%M')


def setTranslationLocale():
    lang = settings['Main'].get('lang', 'en')
    logging.info('Set translation(%s)', lang)
    global trans, transQt
    trans = QTranslator()
    trans.load('lang/' + lang)
    transQt = QTranslator()
    ret = transQt.load('qt_' + lang,
                       QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    if not ret:  # frozen
        transQt.load('lang/qt_' + lang)
    for i in [trans, transQt]: app.installTranslator(i)
    global locale
    locale = QLocale(lang)


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


def setCustomStyleSheet():
    if '-stylesheet' in sys.argv:
        logging.info('Set custom StyleSheet by command line arg')
    elif os.path.isfile('custom.qss'):
        logging.info('Set custom StyleSheet')
        app.setStyleSheet(open('custom.qss').read())


class Fonts:
    """Manage all fonts used in application"""
    def __init__(self):
        self.title = QFont()
        self.date = QFont()
        self.text = QFont()
        self.sys = app.font()
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
app_icon = QIcon(':/appicon16.png')
app_icon.addFile(':/appicon32.png')
app_icon.addFile(':/appicon48.png')
app_icon.addFile(':/appicon64.png')
app.setWindowIcon(app_icon)
# setup fonts after qApp created
font = Fonts()
font.load()

setTranslationLocale()
setCustomStyleSheet()
setDatetimeTrans()

