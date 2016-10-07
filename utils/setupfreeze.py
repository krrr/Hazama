"""Only used to generate frozen binary because of limitation of cx_Freeze."""
import sys
import os
from os import path
from glob import glob
from cx_Freeze import setup, Executable

sys.path[0] = os.getcwd()  # this script will be called by ../setup.py
import hazama
pyqt_dir = os.path.join(sys.exec_prefix, 'lib', 'site-packages', 'PyQt5')


# prepare translation files
ts = list(glob('hazama/lang/*.qm'))  # app's translations
ts += [path.join(pyqt_dir, 'qt', 'translations', 'qt_%s')
       % path.basename(i) for i in ts]  # corresponding Qt translations
all_ts = [(i, '../lang/%s' % path.basename(i)) for i in ts]
main = Executable('hazama.py',
                  base='Console',
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
        'include_files': all_ts,
        'includes': ['PyQt5', 'hazama'],
        'excludes': ['tkinter', 'distutils'],
        'build_exe': 'build/lib',  # dir for exe and dependent files
        'init_script': path.join(os.getcwd(), 'utils', 'cx_freeze_init.py')}},
    executables=[main])
