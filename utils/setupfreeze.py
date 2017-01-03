"""Only used to generate frozen binary because of limitation of cx_Freeze."""
import sys
import os
from os import path
from glob import glob
from cx_Freeze import setup, Executable

sys.path[0] = os.getcwd()  # this script will be called by ../setup.py
import hazama

main = Executable('hazama.py',
                  base='Win32GUI',
                  icon='res/appicon/appicon.ico',
                  appendScriptToLibrary=False,
                  appendScriptToExe=True,
                  targetDir='build')

setup(
    name='Hazama',
    author=hazama.__author__,
    version=hazama.__version__,
    description='Hazama',
    options={'build_exe': {
        'includes': ['PySide.QtCore', 'PySide.QtGui', 'hazama'],
        'excludes': ['tkinter', 'PySide.QtNetwork', 'distutils'],
        'build_exe': 'build/lib',  # dir for exe and dependent files
        'init_script': path.join(os.getcwd(), 'utils', 'cx_freeze_init.py')}},
    executables=[main])
