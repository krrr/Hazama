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
import hazama


class CustomBuild(build):
    # Let build == build_qt and ignore build_py (bad?)
    sub_commands = [('build_qt', lambda self: True)]


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
        # remaining let cx_freeze generate hazama.exe
        os.rename('main.py', 'hazama.py')
        try:
            spawn(['python', pjoin('utils', 'setupfreeze.py'), 'build_exe'])
        finally:
            os.rename('hazama.py', 'main.py')
        # remove duplicate python DLL
        dll_path = glob(pjoin('build', 'python*.dll'))[0]
        os.remove(pjoin('build', 'lib', os.path.basename(dll_path)))


class MakePKGBUILD(Command):
    description = 'Generate PKGBUILD for archlinux'
    user_options = []
    template = """
# Maintainer: krrr <guogaishiwo@gmail.com>
pkgname=hazama
pkgver={ver}
pkgrel=1
pkgdesc="Diary application"
arch=('any')
url="https://krrr.github.io/hazama"
license=('GPL')
depends=('python' 'python-pyside')
makedepends=('python-setuptools' 'python-pyside-tools')
source=("https://github.com/krrr/Hazama/archive/v$pkgver.tar.gz")

build() {{
    cd "$srcdir/Hazama-$pkgver"
    ./setup.py build
}}

package() {{
    cd "$srcdir/Hazama-$pkgver"
    # --skip-build avoid building again when --root specified
    ./setup.py install --root "$pkgdir/" --skip-build
}}
"""

    initialize_options = finalize_options = lambda self: None

    def run(self):
        with open('PKGBUILD', 'w') as f:
            f.write(self.template.strip().format(ver=hazama.__version__))
            f.write('\n')

        os.system('makepkg -g >> PKGBUILD')


if sys.platform == 'win32':
    # fix env variables for PySide tools
    import PySide
    os.environ['PATH'] += ';' + os.path.dirname(PySide.__file__)


# FIXME: PySide installed by archlinux AUR will not recognized by setuptools, so requires not added.
setup(name='Hazama', author=hazama.__author__, version=hazama.__version__,
      description=hazama.__desc__,
      url='https://krrr.github.io/hazama',
      packages=['hazama', 'hazama.ui'],
      package_data={'hazama': ['lang/*.qm']},
      cmdclass={'build': CustomBuild, 'build_qt': BuildQt,
                'update_ts': UpdateTranslations, 'build_exe': BuildExe, 'pkgbuild': MakePKGBUILD},
      zip_safe=False,
      entry_points={'gui_scripts': ['hazama = hazama:main_entry']})
