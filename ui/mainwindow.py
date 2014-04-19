from PySide.QtGui import *
from PySide.QtCore import *
import ui
from ui.customwidgets import SearchBox
from ui.customobjects import SortOrderMenu
from ui.configdialog import ConfigDialog
from .mainwindow_ui import Ui_MainWindow
from config import settings, nikki


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        geo = settings['Main'].get('windowgeo')
        self.restoreGeometry(QByteArray.fromHex(geo))
        self.nlist.load()
        # setup TagList width
        tlist_w = settings['Main'].getint('taglistwidth', 0)
        self.splitter.setSizes([tlist_w, -1])
        # setup sort menu
        s_menu = SortOrderMenu(self)
        s_menu.bydatetime.triggered[bool].connect(self.nlist.sortDT)
        s_menu.bytitle.triggered[bool].connect(self.nlist.sortTT)
        s_menu.bylength.triggered[bool].connect(self.nlist.sortLT)
        s_menu.reverse.triggered[bool].connect(self.nlist.sortRE)
        self.sorAct.setMenu(s_menu)
        sortBtn = self.toolBar.widgetForAction(self.sorAct)
        sortBtn.setPopupMode(QToolButton.InstantPopup)
        # Qt Designer doesn't allow us to add widget in toolbar
        # setup count label
        self.countLabel = QLabel(self.toolBar)
        self.countLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.countLabel.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.countLabel.setIndent(6)
        self.countLabel.setStyleSheet('color: rgb(144, 144, 144)')
        self.updateCountLabel()
        self.toolBar.addWidget(self.countLabel)
        # setup search box
        self.searchBox = SearchBox(self.toolBar)
        self.searchBox.textChanged.connect(self.filter)
        self.toolBar.addWidget(self.searchBox)
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
        settings.save()
        event.accept()
        qApp.quit()

    def filter(self, text=None):
        """Connected to SearchBox and TagList.Argument "text" belongs to SearchBox"""
        text = self.searchBox.text() if text is None else text
        try:
            data = self.tlist.currentItem().data(1)
            tagid = None if data == 'All' else data
        except AttributeError:  # TagList hidden
            tagid = None
        self.nlist.clear()
        self.nlist.load(tagid=tagid, search=text if text else None)

    def retranslate(self):
        """Set translation after language changed in ConfigDialog"""
        ui.set_trans()
        self.retranslateUi(self)
        self.searchBox.retranslate()
        self.updateCountLabel()

    @Slot()
    def on_cfgAct_triggered(self):
        """Start config dialog"""
        try:
            self.cfgDialog.activateWindow()
        except (AttributeError, RuntimeError):
            self.cfgDialog = ConfigDialog(self)
            self.cfgDialog.langChanged.connect(self.retranslate)
            self.cfgDialog.needExport.connect(self.nlist.handleExport)
            self.cfgDialog.bkRestored.connect(self.nlist.reload)
            self.cfgDialog.show()

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
        """Called when diary saving/deleting or on first show"""
        c = nikki.count()
        if c > 1: self.countLabel.setText(self.tr('%i diaries') % c)

    @Slot()
    def on_nlist_reloaded(self):
        self.searchBox.clear()
        self.tlist.setCurrentRow(0)

    @Slot(bool, bool)
    def on_nlist_needRefresh(self, label, tlist):
        if label: self.updateCountLabel()
        if tlist and self.tlist.isVisible(): self.tlist.load()

