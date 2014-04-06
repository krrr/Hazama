from PySide.QtGui import *
from PySide.QtCore import *
from config import settings
import res
import sys
import time
import logging
import locale


def dt_trans_gen():
    dtfmt = settings['Main'].get('datetimefmt', raw=True)
    dfmt = settings['Main'].get('datefmt', raw=True)
    if dtfmt and dfmt:
        def dt_trans(s, dateonly=False):
            try:
                dt = time.strptime(s, '%Y-%m-%d %H:%M')
                return time.strftime(dfmt if dateonly else dtfmt, dt)
            except Exception:
                logging.warning('Failed to translate datetime string')
                return s
    else:
        def dt_trans(s, dateonly=False):
            return s.split()[0] if dateonly else s
    return dt_trans

def currentdt_str():
    return time.strftime('%Y-%m-%d %H:%M')

def set_trans():
    "Install translations"
    lang = settings['Main'].get('lang')
    if lang:
        logging.info('Set translation(%s)', lang)
        global trans, transQt
        trans = QTranslator()
        trans.load('lang/'+lang)
        transQt = QTranslator()
        transQt.load('qt_'+lang, QLibraryInfo.location(QLibraryInfo.TranslationsPath))
        for i in [trans, transQt]: qApp.installTranslator(i)
        windowslangstr = {'zh_CN': 'chinese-simplified', 'en': 'english',
                          'ja_JP': 'japanese'}
        locale.setlocale(locale.LC_ALL, windowslangstr[lang])


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

