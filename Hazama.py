import logging
import sys
import os
import time

__version__ = 0.092


def backupcheck(dbpath):
    """Check backups and do if necessary.Delete old backups."""
    bkpath = 'backup'
    if not os.path.isdir(bkpath): os.mkdir(bkpath)
    dblst = sorted(os.listdir(bkpath))
    fil = lambda x: len(x)>10 and x[4]==x[7]=='-' and x[10]=='_'
    dblst = list(filter(fil, dblst))

    fmt = '%Y-%m-%d'
    today = time.strftime(fmt)
    try:
        newest = dblst[-1]
    except IndexError:  # empty directory
        newest = ''
    if newest.split('_')[0] != today:  # new day
        # make new backup
        import shutil
        shutil.copyfile(dbpath, os.path.join(bkpath,
                                             today+'_%d.db' % nikki.count()))
        logging.info('Everyday backup succeed')
        # delete old backups
        weekbefore = time.strftime(fmt, time.localtime(int(time.time())-604800))
        for dname in dblst:
            if dname < weekbefore:
                os.remove(os.path.join(bkpath, dname))
            else:
                break


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    logging.info('Hazama Version %s', __version__)
    start_time = time.clock()
    from config import settings, nikki
    import ui
    from ui.mainwindow import MainWindow
    mainwindow = MainWindow()
    mainwindow.show()
    logging.debug('Startup take %.2f sec', time.clock()-start_time)
    if settings['Main'].getint('backup', 1): backupcheck(nikki.filepath)
    sys.exit(ui.app.exec_())
