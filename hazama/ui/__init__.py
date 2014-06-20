from PySide.QtGui import QApplication, QIcon, QFont, QFontMetrics, QMessageBox
from PySide.QtCore import QLocale, QTranslator, QLibraryInfo, QDateTime
from config import settings
from ui import rc
import sys
import os
import time
import logging


def dt_trans_gen():
    date_fmt = settings['Main'].get('dateformat', raw=True)
    time_fmt = settings['Main'].get('timeformat', '', raw=True)
    global dt_trans
    if date_fmt:
        def dt_trans(s):
            dt = QDateTime.fromString(s, 'yyyy-MM-dd HH:mm')
            return locale.toString(dt, date_fmt + ' ' + time_fmt)
    else:
        def dt_trans(s): return s


def currentdt_str():
    return time.strftime('%Y-%m-%d %H:%M')


def set_trans():
    """Install Qt translations and set locale"""
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


def show_error_db(hint=''):
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
appicon = QIcon(':/appicon16.png')
appicon.addFile(':/appicon32.png')
appicon.addFile(':/appicon48.png')
appicon.addFile(':/appicon64.png')
app.setWindowIcon(appicon)
# setup fonts after qApp created
font = Fonts()
font.load()
# setup translation
set_trans()
dt_trans_gen()
setCustomStyleSheet()

