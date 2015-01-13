#!/usr/bin/env python3
#   this is main entry of Hazama
#   Copyright (C) 2013 krrr <guogaishiwo@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import logging
import sys
import os
import time


__version__ = '0.21'


if __name__ == '__main__':
    start_time = time.clock()
    try:
        program_path = os.path.dirname(os.path.realpath(__file__))
    except NameError:  # frozen
        program_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(program_path)
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    logging.info('Hazama Version %s', __version__)
    from config import settings
    import ui
    from ui.mainwindow import MainWindow
    mainwindow = MainWindow()
    mainwindow.show()
    logging.debug('startup take %.2f sec', time.clock()-start_time)
    import db
    if settings['Main'].getint('backup', 1):
        db.check_backup()
    sys.exit(ui.app.exec_())
