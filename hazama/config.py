"""Setup database&settings and share them between modules"""
from configparser import ConfigParser
import db
import sys


class ConfigParserSave(ConfigParser):
    """Add save method for convenience"""
    @staticmethod
    def save():
        with open('config.ini', 'w', encoding='utf-8') as f:
            settings.write(f)


# setup settings
settings = ConfigParserSave()
try:
    # utf-8 with BOM will kill ConfigParser
    with open('config.ini', 'r+', encoding='utf-8-sig') as _f:
        settings.read_file(_f)
except FileNotFoundError:
    settings['Main'] = settings['Editor'] = settings['Font'] = {}

# setup database
_db_path = settings['Main'].get('dbpath', 'nikkichou.db')
try:
    nikki = db.Nikki(_db_path)
except db.DatabaseError as e:
    import ui
    ui.showDbError(str(e))
    sys.exit(-1)

