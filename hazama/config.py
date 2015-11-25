"""Setup database & settings and share them between modules"""
from configparser import ConfigParser
import sys
import os
from hazama import db

settings = ConfigParser()
# set default values. some values have no defaults, such as windowGeo and tagListWidth
settings.update({
    'Main': {'debug': False, 'backup': True, 'dbPath': 'nikkichou.db', 'theme': '1px-rect',
             'tagListCount': True, 'extendTitleBarBg': False, 'previewLines': 4,
             'listSortBy': 'datetime', 'listReverse': True, 'tagListVisible': False},
    'Editor': {'autoIndent': True, 'titleFocus': False},
    'Font': {},
    'ThemeColorful': {'colorScheme': 'green'}
})

nikki = db.Nikki()

# set application path (used to load language file)
if hasattr(sys, 'frozen'):
    appPath = os.path.dirname(sys.argv[0])
else:
    appPath = os.path.dirname(__file__)


def changeCWD():
    # user will not care about CWD because this is GUI application?
    if '-portable' in sys.argv:
        os.chdir(appPath)
    else:
        if sys.platform == 'win32':
            p = os.path.join(os.environ['APPDATA'], 'Hazama')
        else:
            cfg_path = os.path.join(os.environ['HOME'], '.config')
            if not os.path.isdir(cfg_path): os.mkdir(cfg_path)
            p = os.path.join(cfg_path, 'Hazama')
        if not os.path.isdir(p): os.mkdir(p)
        os.chdir(p)


def saveSettings():
    try:
        with open('config.ini', 'w', encoding='utf-8') as f:
            settings.write(f)
    except OSError as e:
        from hazama import ui
        ui.showErrors('cantFile', info=str(e))


def init():
    """Load config.ini under CWD, initialize settings and nikki."""
    try:
        # utf-8 with BOM will kill ConfigParser
        with open('config.ini', encoding='utf-8-sig') as f:
            settings.read_file(f)
    except FileNotFoundError:
        pass

    try:
        nikki.connect(settings['Main']['dbPath'])
    except db.DatabaseError as e:
        from hazama import ui
        ui.showErrors('dbError', hint=str(e))
        sys.exit(-1)
    except db.DatabaseLockedError:
        from hazama import ui
        ui.showErrors('dbLocked')
        sys.exit(-1)
