import logging
logging.basicConfig(level=logging.DEBUG)
from PySide.QtGui import *
from PySide.QtCore import *
import ui
from ui.configdialog import ConfigDialog
from ui.nikkitaglist import NikkiList, TagList
from ui.customwidgets import SearchBox
from ui.customobjects import NSplitter, SortOrderMenu
from config import settings, nikki
import sys, os
import time
import random
import locale

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


class MainWindow(QWidget):
    closed = Signal()
    needRestart = Signal()
    def __init__(self):
        super(MainWindow, self).__init__()
        geo = settings['Main'].get('windowgeo')
        self.restoreGeometry(QByteArray.fromHex(geo))
        self.setWindowTitle('Hazama Prototype Ver'+str(__version__))

        self.nlist = NikkiList()
        self.nlist.load()
        self.tlist = TagList()
        self.splitter = NSplitter()
        self.toolbar = QToolBar()
        self.searchbox = SearchBox()
        self.countlabel = QLabel()

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        self.searchbox.textChanged.connect(self.filter)
        self.nlist.needRefresh.connect(self.on_nlist_needRefresh)
        # setuo Splitter
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet('QSplitter::handle{background: rgb(181,61,0)}')
        self.splitter.addWidget(self.tlist)
        self.splitter.addWidget(self.nlist)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)
        tlist_w = settings['Main'].getint('taglistwidth', 0)
        self.splitter.setSizes([tlist_w, -1])

        # setup ToolBar
        self.creActs()  #create actions
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setStyleSheet('QToolBar{background: rgb(242, 241, 231);'
                                   'border-bottom: 1px solid rgb(181, 61, 0);'
                                   'padding: 2px; spacing: 2px}')
        self.sorAct.setMenu(SortOrderMenu(nlist=self.nlist))
        for a in [self.creAct, self.delAct, self.tlistAct, self.sorAct, self.cfgAct]:
            self.toolbar.addAction(a)
        #label
        self.countlabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.countlabel.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.countlabel.setIndent(6)
        self.countlabel.setStyleSheet('color: rgb(144, 144, 144)')
        self.updateCountLabel()
        self.toolbar.addWidget(self.countlabel)

        self.toolbar.addWidget(self.searchbox)
        self.searchbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        sortbtn = self.toolbar.widgetForAction(self.sorAct)
        sortbtn.setPopupMode(QToolButton.InstantPopup)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.splitter)
        self.setLayout(layout)
        if settings['Main'].getint('taglistvisible', 0):
            self.tlistAct.trigger()
        else:
            self.tlist.hide()

    def closeEvent(self, event):
        settings['Main']['windowgeo'] = str(self.saveGeometry().toHex())
        taglistvisible = self.tlist.isVisible()
        settings['Main']['taglistvisible'] = str(taglistvisible.real)
        if taglistvisible:
            settings['Main']['taglistwidth'] = str(self.splitter.sizes()[0])
        self.closed.emit()
        event.accept()

    def filter(self, text=None):
        '''Connected to SearchBox and TagList.Argument "text" belongs to SearchBox'''
        text = self.searchbox.text() if text is None else text
        try:
            data = self.tlist.currentItem().data(1)
            tagid = None if data=='All' else data
        except AttributeError:  # TagList hidden
            tagid = None
        self.nlist.clear()
        self.nlist.load(tagid=tagid, search=text if text else None)

    def creActs(self):
        self.tlistAct = QAction(QIcon(':/images/tlist.png'), self.tr('Tag List'),
                                self, shortcut=QKeySequence(Qt.Key_F9))
        self.tlistAct.setCheckable(True)
        self.tlistAct.triggered[bool].connect(self.toggleTagList)
        self.creAct = QAction(QIcon(':/images/new.png'), self.tr('New'),
                              self, shortcut=QKeySequence.New,
                              triggered=self.nlist.newNikki)
        self.delAct = QAction(QIcon(':/images/delete.png'), self.tr('Delete'),
                              self, triggered=self.nlist.delNikki)
        self.sorAct = QAction(QIcon(':/images/sort.png'), self.tr('Sort By'), self)
        self.cfgAct = QAction(QIcon(':/images/config.png'), self.tr('Settings'),
                              self, triggered=self.startConfigDialog)

    def startConfigDialog(self):
        try:
            self.cfgdialog.activateWindow()
        except (AttributeError, RuntimeError):
            self.cfgdialog = ConfigDialog(self)
            self.cfgdialog.show()

    def toggleTagList(self, checked):
        lst = self.tlist
        lst.setVisible(checked)
        if checked:
            lst.load()
            lst.setCurrentRow(0)
            lst.itemSelectionChanged.connect(self.filter)
        else:
            # currentItem is None when tag deleted
            if lst.currentItem() is None or lst.currentRow()!=0:
                lst.setCurrentRow(0)  # reset filter
            # avoid refreshing nlist by unexpected signal
            lst.itemSelectionChanged.disconnect(self.filter)
            settings['Main']['taglistwidth'] = str(self.splitter.sizes()[0])

    def showEvent(self, event):
        self.nlist.setFocus()

    def updateCountLabel(self):
        "Only called when diary saving or deleting"
        c = nikki.count()
        if c > 1: self.countlabel.setText(self.tr('%i diaries') % c)

    def on_nlist_reloaded(self):
        self.searchbox.clear()
        self.tlist.setCurrentRow(0)

    def on_nlist_needRefresh(self, label, tlist):
        if label: self.updateCountLabel()
        if tlist and self.tlist.isVisible(): self.tlist.load()


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
