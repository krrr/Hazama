from configparser import ConfigParser
from db import Nikki
import os


class ConfigParserSave(ConfigParser):
    """Add save method for convenience"""
    @staticmethod
    def save():
        with open('config.ini', 'w', encoding='utf-8') as f:
            settings.write(f)


_program_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(_program_path)
# setup settings
settings = ConfigParserSave()
try:
    # utf-8 with BOM will kill configparser
    with open('config.ini', 'r+', encoding='utf-8-sig') as f:
        settings.read_file(f)
except FileNotFoundError:
    settings['Main'] = settings['Editor'] = settings['Font'] = {}
# setup database
_dbpath = settings['Main'].get('dbpath', 'nikkichou.db')
nikki = Nikki(_dbpath)

