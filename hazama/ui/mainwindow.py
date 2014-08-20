from PySide.QtGui import *
from PySide.QtCore import *
import ui
from ui.customwidgets import SearchBox, SortOrderMenu
from ui.configdialog import ConfigDialog
from ui.mainwindow_ui import Ui_mainWindow
from config import settings, nikki


class MainWindow(QMainWindow, Ui_mainWindow):
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
        sorMenu.orderChanged.connect(self.nList.sort)
        self.sorAct.setMenu(sorMenu)
        sortBtn = self.toolBar.widgetForAction(self.sorAct)
        sortBtn.setPopupMode(QToolButton.InstantPopup)
        # Qt Designer doesn't allow us to add widget in toolbar
        # setup count label
        self.countLabel = QLabel(self.toolBar)
        self.countLabel.setObjectName('countLabel')
        self.countLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.countLabel.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.countLabel.setIndent(6)
        self.updateCountLabel()
        self.toolBar.addWidget(self.countLabel)
        # setup search box
        self.searchBox = SearchBox(self.toolBar)
        self.searchBox.textChanged.connect(self.nList.setFilterBySearchString)
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

    def retranslate(self):
        """Set translation after language changed in ConfigDialog"""
        ui.setTranslationLocale()
        ui.setDatetimeTrans()
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
            self.cfgDialog.accepted.connect(self.nList.resetDelegate)
            self.cfgDialog.show()

    def toggleTagList(self, checked):
        self.tList.setVisible(checked)
        if checked:
            self.tList.load()
        else:
            self.nList.setFilterByTag('')
            self.tList.clear()
            settings['Main']['taglistwidth'] = str(self.splitter.sizes()[0])

    def showEvent(self, event):
        self.nList.setFocus()

    def updateCountLabel(self):
        """Update label that display count of diaries in Main List"""
        filtered = (self.nList.modelProxy.filterFixedString(0)
                    or self.nList.modelProxy.filterFixedString(1))
        c = self.nList.modelProxy.rowCount() if filtered else self.nList.model.rowCount()
        text = self.tr('%i results') if filtered else self.tr('%i diaries')
        self.countLabel.setText(text % c)

