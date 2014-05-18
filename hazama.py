import db
import logging
import sys
import os
import time

__version__ = 0.10


if __name__ == '__main__':
    start_time = time.clock()
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    logging.info('Hazama Version %s', __version__)
    from config import settings, nikki
    import ui
    from ui.mainwindow import MainWindow
    mainwindow = MainWindow()
    mainwindow.show()
    logging.debug('Startup take %.2f sec', time.clock()-start_time)
    if settings['Main'].getint('backup', 1):
        db.check_backup()
    sys.exit(ui.app.exec_())