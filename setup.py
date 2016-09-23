#!/usr/bin/env python3
import sys
import os
import shutil
import hazama
from os.path import join as pjoin
from glob import glob
from setuptools import setup
from distutils.core import Command
from distutils.errors import DistutilsExecError
from distutils.spawn import find_executable, spawn
from distutils.command.build import build
from setuptools.command.install import install


class CustomBuild(build):
    sub_commands = [('build_qt', lambda self: True)] + build.sub_commands


class CustomInstall(install):
    sub_commands = install.sub_commands + [('desktop_entry', lambda self: sys.platform == 'linux')]


class BuildQt(Command):
    description = 'build Qt files(.ts .ui .rc)'
    user_options = [('ts', 't', 'compile ts files only'),
                    ('ui', 'u', 'compile ui files only'),
                    ('rc', 'r', 'compile rc files only')]

    def initialize_options(self):
        self.ts, self.ui, self.rc = 0, 0, 0

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
        for src in glob(pjoin('hazama', 'ui', '*.ui')):
            dst = src.replace('.ui', '_ui.py')
            if not os.path.isfile(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
                spawn(['pyside-uic', '--from-imports', '-o', dst, '-x', src])

    @staticmethod
    def compile_rc():
        spawn(['pyside-rcc', '-py3', pjoin('res', 'res.qrc'), '-o',
               pjoin('hazama', 'ui', 'res_rc.py')])

    @staticmethod
    def compile_ts():
        lang_dir = pjoin('hazama', 'lang')
        if not os.path.isdir(lang_dir):
            os.mkdir(lang_dir)

        lres = find_executable('lrelease-qt4') or find_executable('lrelease')
        if not lres:
            raise DistutilsExecError('lrelease not found')

        for i in glob(pjoin('translation', '*.ts')):
            qm_filename = os.path.basename(i).split('.')[0] + '.qm'
            spawn([lres, i, '-qm', pjoin(lang_dir, qm_filename)])


class UpdateTranslations(Command):
    description = 'Update translation files'
    user_options = []

    def initialize_options(self): pass

    def finalize_options(self): pass

    def run(self):
        spawn(['pyside-lupdate', pjoin('translation', 'lupdateguide')])


class BuildExe(Command):
    description = 'Call cx_Freeze to build EXE'
    user_options = []

    initialize_options = finalize_options = lambda self: None

    def run(self):
        spawn([sys.executable, pjoin('utils', 'setupfreeze.py'), 'build_exe'])
        # remove duplicate python DLL
        dll_path = glob(pjoin('build', 'python*.dll'))[0]
        os.remove(pjoin('build', 'lib', os.path.basename(dll_path)))


class InstallDesktopEntry(Command):
    description = 'Install .desktop and icon for linux desktop'
    user_options = []
    template = """
[Desktop Entry]
Version={ver}
Type=Application
Name=Hazama
GenericName=Hazama
Comment=Writing diary
Comment[ja]=日記を書く
Comment[zh_CN]=写日记
Icon=hazama
Exec=hazama
NoDisplay=false
Categories=Qt;Utility;
StartupNotify=false
Terminal=false
"""

    initialize_options = finalize_options = lambda self: None

    def run(self):
        # deal with --root option of install when called as sub-command by it
        if sys.argv[1] == 'install' and '--root' in sys.argv:
            root = sys.argv[sys.argv.index('--root')+1]
        else:
            root = '/'
        entry_dir = pjoin(root, 'usr/share/applications/')
        ico_dir = pjoin(root, 'usr/share/pixmaps/')
        if root != '/':
            os.makedirs(entry_dir, exist_ok=True)
            os.makedirs(ico_dir, exist_ok=True)

        with open('Hazama.desktop', 'w') as f:
            f.write(self.template.strip().format(ver=hazama.__version__))
            f.write('\n')
        if not os.path.isdir(entry_dir):
            print('.desktop file has been generated, but program don\'t know where to put it')
            return
        shutil.move('Hazama.desktop', entry_dir)

        if not os.path.isdir(ico_dir):
            print('program don\'t know where to put application icon')
            return
        shutil.copy('res/appicon-64.png', ico_dir + 'hazama.png')


if sys.platform == 'win32':  # fix env variables for PySide tools
    os.environ['PATH'] += ';' + pjoin(sys.exec_prefix, 'lib', 'site-packages', 'PySide')


# PySide installed by linux package manager will not recognized by setuptools, so requires not added.
setup(name='Hazama',
      author=hazama.__author__,
      version=hazama.__version__,
      description=hazama.__desc__,
      url='https://krrr.github.io/hazama',
      packages=['hazama', 'hazama.ui'],
      package_data={'hazama': ['lang/*.qm']},
      cmdclass={'build': CustomBuild, 'build_qt': BuildQt, 'install': CustomInstall,
                'update_ts': UpdateTranslations, 'build_exe': BuildExe,
                'desktop_entry': InstallDesktopEntry},
      zip_safe=False,
      entry_points={'gui_scripts': ['hazama = hazama:main_entry']})
