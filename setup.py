#!/usr/bin/env python
import sys
import os
from os.path import join as pjoin
from glob import glob
from setuptools import setup
from distutils.core import Command
from distutils.errors import DistutilsExecError
from distutils.spawn import find_executable, spawn
from distutils.command.build import build
from hazama import __version__, __author__, __desc__


class CustomBuild(build):
    """Let build == build_qt"""
    def get_sub_commands(self):
        # ignore build_py
        return ['build_qt']


class BuildQt(Command):
    description = 'build Qt files(.ts .ui .rc)'
    user_options = [('ts', 't', 'compile ts files only'),
                    ('ui', 'u', 'compile ui files only'),
                    ('rc', 'r', 'compile rc files only')]

    def initialize_options(self):
        self.ts, self.ui, self.rc = (0,) * 3

    def finalize_options(self): pass

    def run(self):
        methods = [self.compile_ts, self.compile_ui, self.compile_rc]
        for opt, m in zip([self.ts, self.ui, self.rc], methods):
            if opt:
                m()
                break
        else:
            for i in methods: i()

    @staticmethod
    def compile_ui():
        for i in glob(pjoin('hazama', 'ui', '*.ui')):
            spawn(['pyside-uic', '-o', i.split('.')[0]+'_ui.py', '-x', i])
        # fix importing error in generated files
        # resource will be imported in ui.__init__
        for i in glob(pjoin('hazama', 'ui', '*_ui.py')):
            with open(i, 'r', encoding='utf-8') as f:
                text = [l for l in f if not l.startswith('import res_rc')]
            with open(i, 'w', encoding='utf-8') as f:
                f.write(''.join(text))

    @staticmethod
    def compile_rc():
        spawn(['pyside-rcc', '-py3', pjoin('res', 'res.qrc'), '-o',
               pjoin('hazama', 'ui', 'rc.py')])

    @staticmethod
    def compile_ts():
        lang_dir = pjoin('hazama', 'lang')
        if not os.path.isdir(lang_dir): os.mkdir(lang_dir)

        lres = find_executable('lrelease') or find_executable('lrelease-qt4')
        if lres is None:
            raise DistutilsExecError('lrelease not found')

        for i in glob(pjoin('i18n', '*.ts')):
            qm_filename = os.path.basename(i).split('.')[0] + '.qm'
            spawn([lres, i, '-qm', pjoin(lang_dir, qm_filename)])


class UpdateTranslations(Command):
    description = 'Update translation files'
    user_options = []

    def initialize_options(self): pass

    def finalize_options(self): pass

    def run(self):
        spawn(['pyside-lupdate', pjoin('i18n', 'lupdateguide')])


class BuildExe(Command):
    description = 'Call cx_Freeze to build EXE'
    user_options = []

    def initialize_options(self): pass

    def finalize_options(self): pass

    def run(self):
        spawn(['python', 'setupfreeze.py', 'build_exe'])
        # rename exe file (it can't be hazama at first)
        main_path = pjoin('build', 'hazama.exe')
        if os.path.isfile(main_path): os.remove(main_path)
        os.rename(pjoin('build', 'main.exe'), main_path)
        # remove duplicate python DLL
        dll_path = glob(pjoin('build', 'python*.dll'))[0]
        os.remove(pjoin('build', 'lib', os.path.basename(dll_path)))


if sys.platform == 'win32':
    # fix env variables for pyside tools
    import PySide
    pyside_dir = os.path.dirname(PySide.__file__)
    os.environ['PATH'] += ';' + pyside_dir

common_attr = dict()

# FIXME: PySide installed by archlinux AUR will not recognized by setuptools, so requires not added.
setup(name='Hazama', author=__author__, version=__version__,
      description=__desc__,
      url='https://github.com/krrr/Hazama',
      packages=['hazama', 'hazama.ui'],
      package_data={'hazama': ['lang/*.qm']},
      cmdclass={'build': CustomBuild, 'build_qt': BuildQt,
                'update_ts': UpdateTranslations, 'build_exe': BuildExe},
      zip_safe=False,
      entry_points={'gui_scripts': ['hazama = hazama.mainentry:main']},
      **common_attr)
