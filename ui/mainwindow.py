from PySide.QtGui import *
from PySide.QtCore import *
from ui.customwidgets import SearchBox
from ui.customobjects import SortOrderMenu
from ui.configdialog import ConfigDialog
from .mainwindow_ui import Ui_MainWindow
from config import settings, nikki


class MainWindow(QMainWindow, Ui_MainWindow):
    closed = Signal()
    needRestart = Signal()

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        geo = settings['Main'].get('windowgeo')
        self.restoreGeometry(QByteArray.fromHex(geo))
        self.nlist.load()
        # setuo TagList width
        tlist_w = settings['Main'].getint('taglistwidth', 0)
        self.splitter.setSizes([tlist_w, -1])
        # setup sort menu
        self.sorAct.setMenu(SortOrderMenu(nlist=self.nlist))
        sortbtn = self.toolBar.widgetForAction(self.sorAct)
        sortbtn.setPopupMode(QToolButton.InstantPopup)
        # Qt Designer doesn't allow us to add widget in toolbar
        # setup count label
        self.countlabel = QLabel(self.toolBar)
        self.countlabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.countlabel.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.countlabel.setIndent(6)
        self.countlabel.setStyleSheet('color: rgb(144, 144, 144)')
        self.updateCountLabel()
        self.toolBar.addWidget(self.countlabel)
        # setup search box
        self.searchbox = SearchBox(self.toolBar)
        self.searchbox.textChanged.connect(self.filter)
        # self.searchbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.toolBar.addWidget(self.searchbox)
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
        """Connected to SearchBox and TagList.Argument "text" belongs to SearchBox"""
        text = self.searchbox.text() if text is None else text
        try:
            data = self.tlist.currentItem().data(1)
            tagid = None if data == 'All' else data
        except AttributeError:  # TagList hidden
            tagid = None
        self.nlist.clear()
        self.nlist.load(tagid=tagid, search=text if text else None)

    @Slot()
    def on_cfgAct_triggered(self):
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
            if lst.currentItem() is None or lst.currentRow() != 0:
                lst.setCurrentRow(0)  # reset filter
            # avoid refreshing nlist by unexpected signal
            lst.itemSelectionChanged.disconnect(self.filter)
            settings['Main']['taglistwidth'] = str(self.splitter.sizes()[0])

    def showEvent(self, event):
        self.nlist.setFocus()

    def updateCountLabel(self):
        """Only called when diary saving or deleting"""
        c = nikki.count()
        if c > 1: self.countlabel.setText(self.tr('%i diaries') % c)

    @Slot()
    def on_nlist_reloaded(self):
        self.searchbox.clear()
        self.tlist.setCurrentRow(0)

    @Slot(bool, bool)
    def on_nlist_needRefresh(self, label, tlist):
        if label: self.updateCountLabel()
        if tlist and self.tlist.isVisible(): self.tlist.load()

