#!/usr/bin/env python3
import sys
import os
from os import path
from glob import glob
from distutils.core import Command
from distutils.spawn import find_executable


class build_qt(Command):
    description = 'build Qt files(.ts .ui .rc)'
    user_options = [('ts', 't', 'compile ts files only'),
                    ('ui', 'u', 'compile ui files only'),
                    ('rc', 'r', 'compile rc files only')]

    def initialize_options(self):
        self.ts, self.ui, self.rc = (0,) * 3

    def finalize_options(self): pass

    def run(self):
        methods = [self.compile_ts, self.compile_ui, self.compile_rc]
        for a, m in zip([self.ts, self.ui, self.rc], methods):
            if a:
                m()
                break
        else:
            for i in methods: i()

    @staticmethod
    def compile_ui():
        for i in glob(path.join('hazama', 'ui', '*.ui')):
            os.system('pyside-uic -o %s -x %s' % (i.split('.')[0]+'_ui.py', i))
        # fix importing error in generated files
        for i in glob(path.join('hazama', 'ui', '*_ui.py')):
            with open(i, 'r', encoding='utf-8') as f:
                new = []
                for l in f:
                    # resource will be imported in ui.__init__
                    if l.startswith('import res_rc'): continue
                    if l.startswith('from') and not l.startswith('from PySide'):
                        l = l.replace('from ', 'from ui.')
                    new.append(l)
                new = ''.join(new)
            with open(i, 'w', encoding='utf-8', newline='\n') as f:
                f.write(new)
        print('ui compiled successfully')

    @staticmethod
    def compile_rc():
        os.system('pyside-rcc -py3 %s -o %s' % (path.join('res', 'res.qrc'),
                                                path.join('hazama', 'ui', 'rc.py')))
        print('rc compiled successfully')

    @staticmethod
    def compile_ts():
        lang_dir = path.join('hazama', 'lang')
        if not path.isdir(lang_dir): os.mkdir(lang_dir)
        lres = 'lrelease' if find_executable('lrelease') else 'lrelease-qt4'
        for i in glob(path.join('i18n', '*.ts')):
            qm_filename = path.basename(i).split('.')[0] + '.qm'
            os.system('%s %s -qm %s' % (lres, i,
                                        path.join(lang_dir, qm_filename)))


class update_ts(Command):
    description = 'Update translation files'
    user_options = []

    def initialize_options(self): pass

    def finalize_options(self): pass

    def run(self):
        os.system('pyside-lupdate %s' % path.join('i18n', 'lupdateguide'))
        print('ts updated successfully')


cmdclass = {'build_qt': build_qt, 'update_ts': update_ts}

if sys.platform == 'win32':
    import PySide
    pyside_dir = path.dirname(PySide.__file__)
    os.environ['PATH'] += ';' + pyside_dir

if sys.platform == 'win32' and 'build' in sys.argv:
    from cx_Freeze import setup, Executable

    # prepare translation files
    ts = [i for i in glob('hazama/lang/*.qm')]
    qt_ts = [path.join(pyside_dir, 'translations', 'qt_%s')
             % path.basename(i) for i in ts]
    all_ts = [(i, '../lang/%s' % path.basename(i)) for i in ts + qt_ts]
    main = Executable('hazama/hazama.py',
                      base='Win32GUI',
                      icon='res/appicon/appicon.ico',
                      appendScriptToLibrary=False,
                      appendScriptToExe=True,
                      targetDir='build')
    extra_opts = dict(
        options={'build_exe': {
            'include_files': all_ts,
            'includes': ['PySide.QtCore', 'PySide.QtGui'],
            'excludes': ['tkinter', 'PySide.QtNetwork', 'distutils'],
            'build_exe': 'build/lib',
            'path': sys.path + ['hazama/'],
            'init_script': path.join(os.getcwd(), 'utils', 'cx_freeze_init.py')}},
        executables=[main])
else:
    from distutils.core import setup
    extra_opts = {}


setup(name='Hazama',
      author='krrr',
      url='https://github.com/krrr/Hazama',
      version="0.14",
      description='A simple cross-platform diary program',
      requires=['PySide'],
      cmdclass=cmdclass,
      **extra_opts)

