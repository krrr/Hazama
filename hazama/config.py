"""Setup database & settings and share them between modules"""
import sys
import os
from configparser import ConfigParser, ParsingError
from os import path
from hazama import diarybook


# constants
SOCKET_TIMEOUT = 8
CUSTOM_STYLESHEET_DELIMIT = '/**** BEGIN CUSTOM STYLESHEET ****/'

# for default settings
isWin = hasattr(sys, 'getwindowsversion')
winVer = sys.getwindowsversion() if isWin else None
isWinVistaOrLater = isWin and winVer >= (6, 0)
isWin7 = isWin and winVer[:2] == (6, 1)
isWin7OrLater = isWin and winVer >= (6, 1)
isWin8 = isWin and winVer[:2] == (6, 2)
isWin8OrLater = isWin and winVer >= (6, 2)
# isWin10OrLater requires manifest file on old Py versions (<= 3.4)
isWin10 = isWin and winVer >= (10, 0)

settings = ConfigParser()
# set default values. some values have no defaults, such as windowGeo and tagListWidth
settings.update({
    'Main': {'debug': False,
             'lang': 'en',
             'backup': True,
             'dbPath': 'nikkichou.db',
             'tagListCount': True,
             'previewLines': 4,
             'listSortBy': 'datetime',
             'listReverse': True,
             'listAnnotated': True,
             'tagListVisible': False,
             'extendTitleBarBg': isWin8OrLater,  # Win8 has no aero glass
             'theme': 'colorful' if isWinVistaOrLater else '1px-rect'},
    'Editor': {'autoIndent': False,
               'titleFocus': False,
               'autoReadOnly': True,
               'tabIndent': True},
    'Font': {'enhanceRender': False},  # for default fonts, see Font.load
    'Update': {'autoCheck': False,
               'newestIgnoredVer': '0.0.0',
               'needClean': False},
    'ThemeColorful': {'colorScheme': 'green'}
})

db = diarybook.DiaryBook()

# set application path (used to load language file)
if hasattr(sys, 'frozen'):
    appPath = path.dirname(sys.argv[0])
else:
    appPath = path.dirname(__file__)


def changeCWD():
    # user will not care about CWD because this is GUI application?
    if '-portable' in sys.argv or path.isfile(path.join(appPath, 'config.ini')):
        os.chdir(appPath)
    else:
        if sys.platform == 'win32':
            p = path.join(os.environ['APPDATA'], 'Hazama')
        else:
            cfg_path = path.join(os.environ['HOME'], '.config')
            if not path.isdir(cfg_path): os.mkdir(cfg_path)
            p = path.join(cfg_path, 'Hazama')
        if not path.isdir(p): os.mkdir(p)
        os.chdir(p)


def saveSettings():
    try:
        with open('config.ini', 'w', encoding='utf-8') as f:
            settings.write(f)
    except OSError:
        from hazama import ui
        ui.showErrors('cantFile', 'config.ini')


def init():
    """Load config.ini under CWD, initialize settings and diary book."""
    try:
        # utf-8 with BOM will kill ConfigParser
        with open('config.ini', encoding='utf-8-sig') as f:
            settings.read_file(f)
    except ParsingError:
        from hazama import ui
        ui.showErrors('fileCorrupted', 'config.ini', exit_=True)
    except FileNotFoundError:
        pass

    try:
        db.connect(settings['Main']['dbPath'])
    except diarybook.DatabaseError as e:
        from hazama import ui
        if str(e).startswith('unable to open'):
            ui.showErrors('cantFile', settings['Main']['dbPath'], exit_=True)
        else:
            ui.showErrors('dbError', str(e), exit_=True)
    except diarybook.DatabaseLockedError:
        from hazama import ui
        ui.showErrors('dbLocked', exit_=True)
