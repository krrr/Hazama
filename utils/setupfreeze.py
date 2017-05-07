"""Only used to generate frozen binary because of limitation of cx_Freeze.
5.0 bugs:
1. sqlite3.dll not copied
2. will search dlls in lib directory (undocumented) so custom initScript is unnecessary
3. include many unused modules (specify them in options to reduce size ~0.7MB)
"""
import sys
import os
import cx_Freeze
from os import path
from glob import glob
from cx_Freeze import setup, Executable

if not cx_Freeze.version.startswith('5'):
    print('cx_Freeze 5.0 or higher required')
    sys.exit(-1)


sys.path[0] = os.getcwd()  # this script will be called by ../setup.py
import hazama

main_exe = Executable('hazama.py',
                      base='Win32GUI',
                      icon='res/appicon/appicon.ico')

setup(
    name='Hazama',
    author=hazama.__author__,
    version=hazama.__version__,
    description='Hazama',
    options={'build_exe': {
        'includes': ['PySide.QtCore', 'PySide.QtGui', 'hazama'],
        'excludes': ['PySide.QtNetwork', 'PySide.QtXml',
                     'win32evtlogutil', 'win32evtlog', 'plistlib', 'pyreadline',
                     'pydoc', 'unittest', 'doctest', 'inspect'],
        'zip_include_packages': ['*'],
        'zip_exclude_packages': [],
    }},
    executables=[main_exe])
