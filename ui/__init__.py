from PySide.QtGui import QApplication, QIcon, QFont, QFontMetrics
from PySide.QtCore import QLocale, QTranslator, QLibraryInfo, QDateTime
from config import settings
from . import icons_rc
import sys
import time
import logging


def dt_trans_gen():
    datefmt = settings['Main'].get('dateformat', raw=True)
    timefmt = settings['Main'].get('timeformat', '', raw=True)
    if datefmt:
        def dt_trans(s):
            dt = QDateTime.fromString(s, 'yyyy-MM-dd HH:mm')
            return locale.toString(dt, datefmt + ' ' + timefmt)
    else:
        def dt_trans(s): return s
    return dt_trans


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
    transQt.load('qt_' + lang,
                 QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    for i in [trans, transQt]: app.installTranslator(i)
    global locale
    locale = QLocale(lang)


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
appicon.addFile(':/appicon64.png')
app.setWindowIcon(appicon)
# setup fonts after qApp created
font = Fonts()
font.load()
# setup translation
set_trans()
dt_trans = dt_trans_gen()

