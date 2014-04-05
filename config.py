from configparser import ConfigParser
import os


class ConfigParserSave(ConfigParser):
    "Add save method for convience"
    @staticmethod
    def save():
        with open('config.ini', 'w', encoding='utf-8') as f:
            settings.write(f)


program_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(program_path)
# set settings
settings = ConfigParserSave()
try:
    with open('config.ini', 'r+', encoding='utf-8') as f:
        settings.read_file(f)
except FileNotFoundError:
    settings['Main'] = settings['Editor'] = settings['Font'] = {}

