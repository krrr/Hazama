#!/usr/bin/env python3
import logging
import sys
import os
import time


__version__ = 0.14


if __name__ == '__main__':
    start_time = time.clock()
    try:
        program_path = os.path.dirname(os.path.realpath(__file__))
    except NameError:  # frozen
        program_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    os.chdir(program_path)
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    logging.info('Hazama Version %s', __version__)
    from config import settings
    import ui
    from ui.mainwindow import MainWindow
    mainwindow = MainWindow()
    mainwindow.show()
    logging.debug('Startup take %.2f sec', time.clock()-start_time)
    import db
    if settings['Main'].getint('backup', 1):
        db.check_backup()
    sys.exit(ui.app.exec_())
