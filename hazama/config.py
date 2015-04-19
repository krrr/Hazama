"""Setup database & settings and share them between modules"""
from configparser import ConfigParser
import sys
import os
from hazama import db

settings = nikki = None

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
    with open('config.ini', 'w', encoding='utf-8') as f:
        settings.write(f)


def init():
    """Load config.ini under CWD, initialize settings and nikki."""
    global settings
    settings = ConfigParser()
    try:
        # utf-8 with BOM will kill ConfigParser
        with open('config.ini', encoding='utf-8-sig') as f:
            settings.read_file(f)
    except FileNotFoundError:
        for i in ['Main', 'Editor', 'Font']:
            settings[i] = {}

    global nikki
    db_path = settings['Main'].get('dbpath', 'nikkichou.db')
    try:
        nikki = db.Nikki(db_path)
    except db.DatabaseError as e:
        from hazama import ui
        ui.showDbError(str(e))
        sys.exit(-1)
    except db.DatabaseLockedError:
        from hazama import ui
        ui.showDbLockedError()
        sys.exit(-1)
