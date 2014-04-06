import logging
logging.basicConfig(level=logging.DEBUG)
import ui
from ui.mainwindow import MainWindow
from config import settings, nikki
import sys, os
import time

__version__ = 0.09


def backupcheck(dbpath):
    "Check backups and do if necessary.Delete old backups."
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
        weekbefore = time.strftime(fmt , time.localtime(int(time.time())-604800))
        for dname in dblst:
            if dname < weekbefore:
                os.remove(os.path.join(bkpath, dname))
            else:
                break


class Hazama:
    def __init__(self):
        self.setMainWindow()

    def quit(self):
        settings.save()
        ui.app.quit()

    def restartMainWindow(self):
        "Restart after language changed in settings."
        ui.set_trans()
        geo = self.mainw.saveGeometry()
        self.setMainWindow()
        self.mainw.restoreGeometry(geo)

    def setMainWindow(self):
        self.mainw = MainWindow()
        self.mainw.closed.connect(self.quit)
        self.mainw.needRestart.connect(self.restartMainWindow)
        self.mainw.show()



if __name__ == '__main__':
    timee = time.clock()
    hazama = Hazama()
    logging.debug('startup take %s seconds' % round(time.clock()-timee,3))
    if settings['Main'].getint('backup', 1): backupcheck(nikki.filepath)
    sys.exit(ui.app.exec_())
