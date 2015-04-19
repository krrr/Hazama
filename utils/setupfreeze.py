"""Only used to generate freeze binary because of limitation of cx_Freeze."""
import sys
import os
from os import path
from glob import glob
import PySide
from cx_Freeze import setup, Executable

sys.path[0] = os.getcwd()  # this script will called by ../setup.py
from hazama import __version__, __author__, __desc__

pyside_dir = path.dirname(PySide.__file__)


# prepare translation files
ts = list(glob('hazama/lang/*.qm'))  # application's translations
ts += [path.join(pyside_dir, 'translations', 'qt_%s')
       % path.basename(i) for i in ts]  # corresponding Qt translations
all_ts = [(i, '../lang/%s' % path.basename(i)) for i in ts]
main = Executable('main.py',
                  base='Win32GUI',
                  icon='res/appicon/appicon.ico',
                  appendScriptToLibrary=False,
                  appendScriptToExe=True,
                  targetDir='build')

setup(
    name='Hazama', author=__author__, version=__version__, description=__desc__,
    options={'build_exe': {
        'include_files': all_ts,
        'includes': ['PySide.QtCore', 'PySide.QtGui', 'hazama'],
        'excludes': ['tkinter', 'PySide.QtNetwork', 'distutils'],
        'build_exe': 'build/lib',  # dir for exe and dependent files
        'init_script': path.join(os.getcwd(), 'utils', 'cx_freeze_init.py')}},
    executables=[main])
