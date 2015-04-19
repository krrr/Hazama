import logging
import time
from hazama import __version__, db, config


def main():
    start_time = time.clock()
    config.changeCWD()
    config.setSettings()
    # setup logging
    logging.basicConfig(
        format='%(levelname)s: %(message)s', level=logging.DEBUG if
        config.settings['Main'].getboolean('debug') else logging.INFO)
    logging.info('Hazama v%s', __version__)
    config.setNikki()

    from hazama.ui import app  # initialize UI
    from hazama.ui.mainwindow import MainWindow
    w = MainWindow()
    w.show()
    logging.debug('startup took %.2f sec', time.clock()-start_time)

    if config.settings['Main'].getboolean('backup', True):
        db.check_backup()
    return app.exec_()
