"""Setup database & settings and share them between modules"""
from configparser import ConfigParser
import sys
import logging
import db

settings = nikki = None


def setSettings():
    global settings
    settings = ConfigParser()
    try:
        # utf-8 with BOM will kill ConfigParser
        with open('config.ini', encoding='utf-8-sig') as f:
            settings.read_file(f)
    except FileNotFoundError:
        settings['Main'] = settings['Editor'] = settings['Font'] = {}


def saveSettings():
    with open('config.ini', 'w', encoding='utf-8') as f:
        settings.write(f)


def setNikki():
    global nikki
    db_path = settings['Main'].get('dbpath', 'nikkichou.db')
    try:
        nikki = db.Nikki(db_path)
        logging.info(str(nikki))
    except db.DatabaseError as e:
        import ui
        ui.showDbError(str(e))
        sys.exit(-1)
    except db.DatabaseLockedError:
        import ui
        ui.showDbLockedError()
        sys.exit(-1)
