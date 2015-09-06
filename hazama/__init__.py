# Copyright (C) 2015 krrr <guogaishiwo@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
__version__ = '0.32'
__desc__ = 'A simple cross-platform diary application'
__author__ = 'krrr'


def main_entry():
    import time
    import logging
    from hazama import db, config

    start_time = time.clock()
    config.changeCWD()
    config.init()
    # setup logging
    level = logging.DEBUG if config.settings['Main'].getboolean('debug') else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=level)
    logging.info('Hazama v%s', __version__)
    logging.info(str(config.nikki))

    from hazama.ui import app  # initialize UI
    from hazama.ui.mainwindow import MainWindow
    w = MainWindow()
    w.show()
    logging.debug('startup took %.2f sec', time.clock()-start_time)

    if config.settings['Main'].getboolean('backup'):
        try:
            db.backup()
        except OSError as e:
            from hazama.ui import showErrors
            showErrors('cantFile', info=str(e))
    return app.exec_()
