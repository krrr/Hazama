from PySide.QtGui import *
from PySide.QtCore import *
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
            return locale.toString(dt, datefmt+' '+timefmt)
    else:
        def dt_trans(s): return s
    return dt_trans

def currentdt_str():
    return time.strftime('%Y-%m-%d %H:%M')

def set_trans():
    "Install Qt ranslations and set locale"
    lang = settings['Main'].get('lang', 'en')
    logging.info('Set translation(%s)', lang)
    global trans, transQt
    trans = QTranslator()
    trans.load('lang/'+lang)
    transQt = QTranslator()
    transQt.load('qt_'+lang, QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    for i in [trans, transQt]: qApp.installTranslator(i)
    global locale
    locale = QLocale(lang)


class Fonts:
    def __init__(self):
        self.title = QFont()
        self.title.fromString(settings['Font'].get('title'))
        self.title_m = QFontMetrics(self.title)
        self.date = QFont()
        self.date.fromString(settings['Font'].get('datetime'))
        self.date_m = QFontMetrics(self.date)
        self.text = QFont()
        self.text.fromString(settings['Font'].get('text'))
        self.sys = app.font()
        if settings['Font'].get('default'):
            self.default = QFont()
            self.default.fromString(settings['Font'].get('default'))
            app.setFont(self.default)
        else:
            self.default = _appfont
        self.default_m = QFontMetrics(self.default)


# setup application icon
app = QApplication(sys.argv)
appicon = QIcon(':/appicon16.png')
appicon.addFile(':/appicon32.png')
appicon.addFile(':/appicon64.png')
app.setWindowIcon(appicon)
# setup fonts after qApp created
font = Fonts()
# setup translation
set_trans()
dt_trans = dt_trans_gen()

