#!/usr/bin/env python3
import sys
import os
import shutil
import hazama
from os.path import join as pjoin
from glob import glob
from setuptools import setup
from distutils.sysconfig import get_python_lib
from distutils.core import Command
from distutils.errors import DistutilsExecError
from distutils.spawn import find_executable, spawn
from distutils.command.build import build
from setuptools.command.install import install
from distutils.command.clean import clean


class CustomBuild(build):
    sub_commands = [('build_qt', lambda self: True)] + build.sub_commands


class CustomInstall(install):
    _desktop_template = """
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

    def run(self):
        super().run()
        if sys.platform == 'win32':
            return

        entry_dir = pjoin(self.root, 'usr/share/applications/')
        svg_dir = pjoin(self.root, 'usr/share/icons/hicolor/scalable/apps/')
        png_dir = pjoin(self.root, 'usr/share/icons/hicolor/48x48/apps/')
        for i in (entry_dir, svg_dir, png_dir):
            os.makedirs(i, exist_ok=True)

        with open(entry_dir + 'Hazama.desktop', 'w') as f:
            f.write(self._desktop_template.strip().format(ver=hazama.__version__))
            f.write('\n')

        shutil.copy('res/appicon/appicon-64.svg', svg_dir + 'hazama.svg')
        shutil.copy('res/appicon-48.png', png_dir + 'hazama.png')


class BuildQt(Command):
    description = 'build Qt files(.ts .ui .rc)'
    user_options = [('ts', 't', 'compile ts files only'),
                    ('ui', 'u', 'compile ui files only'),
                    ('rc', 'r', 'compile rc files only')]

    def initialize_options(self):
        # noinspection PyAttributeOutsideInit
        self.ts = self.ui = self.rc = False
        self.force = False

    def finalize_options(self): pass

    def run(self):
        methods = ('ts', 'ui', 'rc')
        opts = tuple(filter(lambda x: getattr(self, x), methods))
        if opts:
            self.force = True
        else:
            opts = methods  # run all methods if no options passed

        for i in opts:
            getattr(self, 'compile_'+i)()

    def compile_ui(self):
        for src in glob(pjoin('hazama', 'ui', '*.ui')):
            dst = src.replace('.ui', '_ui.py')
            if self.force or (not os.path.isfile(dst) or
                              os.path.getmtime(src) > os.path.getmtime(dst)):
                spawn(['pyside-uic', '--from-imports', '-o', dst, '-x', src])

    @staticmethod
    def compile_rc():
        spawn(['pyside-rcc', '-py3', pjoin('res', 'res.qrc'), '-o',
               pjoin('hazama', 'ui', 'res_rc.py')])

    @staticmethod
    def compile_ts():
        lang_dir = pjoin('build', 'lang')
        if not os.path.isdir(lang_dir):
            os.makedirs(lang_dir)

        lres = find_executable('lrelease-qt4') or find_executable('lrelease')
        if not lres:
            raise DistutilsExecError('lrelease not found')

        trans = [os.path.basename(i).split('.')[0] for i in
                 glob(pjoin('translation', '*.ts'))]
        for i in trans:
            spawn([lres, pjoin('translation', i+'.ts'), '-qm', pjoin(lang_dir, i+'.qm')])

        if sys.platform != 'win32':
            return
        # copy corresponding Qt translations to build/lang
        pyside_dir = pjoin(get_python_lib(), 'PySide')
        for i in trans:
            target = pjoin(lang_dir, 'qt_%s.qm' % i)
            if not os.path.isfile(target):
                print('copy to ' + target)
                shutil.copy(pjoin(pyside_dir, 'translations', 'qt_%s.qm' % i), target)


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
        spawn([sys.executable, pjoin('utils', 'setupfreeze5.py'), 'build_exe'])
        # remove duplicate python DLL
        try:
            dll_path = glob(pjoin('build', 'python*.dll'))[0]
            os.remove(pjoin('build', 'lib', os.path.basename(dll_path)))
        except IndexError:
            pass


class Clean(clean):
    def run(self):
        super().run()
        for i in glob(pjoin('hazama', 'ui', '*_ui.py')):
            print('remove file: ' + i)
            os.remove(i)
        for i in ['build', pjoin('hazama', 'ui', 'res_rc.py')]:
            if os.path.isfile(i):
                print('remove file: ' + i)
                os.remove(i)
            elif os.path.isdir('build'):
                print('remove dir: ' + i)
                shutil.rmtree('build')


# fix env variables for PySide tools
if sys.platform == 'win32':
    os.environ['PATH'] += (';' + pjoin(sys.exec_prefix, 'Scripts') +
                           ';' + pjoin(sys.exec_prefix, 'lib', 'site-packages', 'PySide'))


# PySide installed by linux package manager will not recognized by setuptools, so requires not added.
setup(name='Hazama',
      author='krrr',
      author_email='guogaishiwo@gmail.com',
      version=hazama.__version__,
      description=hazama.__desc__,
      url='https://krrr.github.io/hazama',
      packages=['hazama', 'hazama.ui'],
      cmdclass={'build': CustomBuild, 'build_qt': BuildQt, 'install': CustomInstall,
                'update_ts': UpdateTranslations, 'build_exe': BuildExe, 'clean': Clean},
      zip_safe=True,
      entry_points={'gui_scripts': ['hazama = hazama:main_entry']})
