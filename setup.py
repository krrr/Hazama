import sys
from os import path
from glob import glob
from cx_Freeze import setup, Executable


program_path = path.dirname(path.realpath(__file__))
import PySide
pyside_dir = path.dirname(PySide.__file__)
# prepare translation files
trs = [i for i in glob('lang/*.qm')]
qt_trs = [path.join(pyside_dir, 'translations', 'qt_%s')
          % path.basename(i) for i in trs]
all_trans = [(i, '../lang/%s' % path.basename(i)) for i in trs + qt_trs]


main = Executable('hazama.py',
                  base='Win32GUI',
                  icon='res/appicon/appicon.ico',
                  appendScriptToLibrary=False,
                  appendScriptToExe=True,
                  copyDependentFiles=False,
                  targetDir='build')
                  
freeze_opts = dict(
    options={'build_exe': {
        'include_files': all_trans,
        'includes': ['PySide.QtCore', 'PySide.QtGui'],
        'excludes': ['tkinter', 'PySide.QtNetwork', 'distutils'],
        'build_exe': 'build/lib',
        'init_script': path.join(program_path, 'utils', 'cx_freeze_init.py')}},
    executables=[main])
    

setup(name='Hazama',
      author='krrr',
      url='https://github.com/krrr/Hazama',
      version="0.11",
      description='Hazama the diary program',
      requires=['PySide'],
      **freeze_opts)
