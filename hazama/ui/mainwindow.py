from PySide.QtGui import *
from PySide.QtCore import *
import ui
from ui.customwidgets import SearchBox, SortOrderMenu
from ui.configdialog import ConfigDialog
from ui.mainwindow_ui import Ui_MainWindow
from config import settings, nikki


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.cfgDialog = None  # create on on_cfgAct_triggered
        geo = settings['Main'].get('windowgeo')
        self.restoreGeometry(QByteArray.fromHex(geo))
        # self.nList.load()
        # setup TagList width
        tListW = settings['Main'].getint('taglistwidth', 0)
        if not self.isMaximized():
            self.splitter.setSizes([tListW, self.width()-tListW])
        # setup sort menu
        sorMenu = SortOrderMenu(self)
        # sorMenu.datetime.triggered[bool].connect(self.nList.sortDT)
        # sorMenu.title.triggered[bool].connect(self.nList.sortTT)
        # sorMenu.length.triggered[bool].connect(self.nList.sortLT)
        # sorMenu.reverse.triggered[bool].connect(self.nList.sortRE)
        self.sorAct.setMenu(sorMenu)
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
            self.tListAct.trigger()
        else:
            self.tList.hide()

    def closeEvent(self, event):
        settings['Main']['windowgeo'] = str(self.saveGeometry().toHex())
        tListVisible = self.tList.isVisible()
        settings['Main']['taglistvisible'] = str(tListVisible .real)
        if tListVisible:
            settings['Main']['taglistwidth'] = str(self.splitter.sizes()[0])
        settings.save()
        event.accept()
        qApp.quit()

    def filter(self, text=None):
        """Connected to SearchBox and TagList.Argument "text" belongs to SearchBox"""
        text = self.searchBox.text() if text is None else text
        try:
            data = self.tList.currentItem().data(1)
            tagId = None if data == 'All' else data
        except AttributeError:  # TagList hidden
            tagId = None
        self.nList.clear()
        self.nList.load(tagId=tagId, search=text if text else None)

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
            self.cfgDialog.needExport.connect(self.nList.handleExport)
            self.cfgDialog.bkRestored.connect(self.nList.reload)
            self.cfgDialog.accepted.connect(self.nList.reloadWithDgReset)
            self.cfgDialog.show()

    def toggleTagList(self, checked):
        lst = self.tList
        lst.setVisible(checked)
        if checked:
            lst.load()
            lst.setCurrentRow(0)
            lst.itemSelectionChanged.connect(self.filter)
        else:
            # currentItem is None when tag deleted
            if lst.currentItem() is None or lst.currentRow() != 0:
                lst.setCurrentRow(0)  # reset filter
            # avoid refreshing nList by unexpected signal
            lst.itemSelectionChanged.disconnect(self.filter)
            settings['Main']['taglistwidth'] = str(self.splitter.sizes()[0])

    def showEvent(self, event):
        self.nList.setFocus()

    def updateCountLabel(self):
        """Called when diary saving/deleting or on first show"""
        c = nikki.count()
        if c > 1: self.countLabel.setText(self.tr('%i diaries') % c)

    @Slot()
    def on_nList_reloaded(self):
        self.searchBox.clear()
        self.tList.setCurrentRow(0)

    @Slot(bool, bool)
    def on_nList_needRefresh(self, label, tList):
        if label: self.updateCountLabel()
        if tList and self.tList.isVisible(): self.tList.load()

