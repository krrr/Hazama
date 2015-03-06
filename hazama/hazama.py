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
from os import path
import time
import db
import config


__version__ = '0.3'


if __name__ == '__main__':
    start_time = time.clock()
    # change CWD to application's path
    # user will not care about CWD because this is GUI application?
    try:
        app_path = path.dirname(path.realpath(__file__))
    except NameError:  # frozen
        app_path = path.dirname(sys.argv[0])
    os.chdir(app_path)
    config.setSettings()
    # setup logging
    logging.basicConfig(
        format='%(levelname)s: %(message)s', level=logging.DEBUG if
        config.settings['Main'].getboolean('debug') else logging.INFO)
    logging.info('Hazama Version %s', __version__)
    config.setNikki()

    from ui import app  # initialize UI
    from ui.mainwindow import MainWindow
    w = MainWindow()
    w.show()
    logging.debug('startup take %.2f sec', time.clock()-start_time)

    if config.settings['Main'].getboolean('backup', True):
        db.check_backup()
    sys.exit(app.exec_())
