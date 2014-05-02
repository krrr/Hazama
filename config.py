"""Setup database&settings, set work directory,
and share global variables between modules"""
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
if _program_path.endswith('.zip'):  # path is a frozen library
    _program_path = os.path.dirname(_program_path)
os.chdir(_program_path)
# setup settings
settings = ConfigParserSave()
try:
    # utf-8 with BOM will kill ConfigParser
    with open('config.ini', 'r+', encoding='utf-8-sig') as _f:
        settings.read_file(_f)
except FileNotFoundError:
    settings['Main'] = settings['Editor'] = settings['Font'] = {}
# setup database
_dbpath = settings['Main'].get('dbpath', 'nikkichou.db')
nikki = Nikki(_dbpath)

