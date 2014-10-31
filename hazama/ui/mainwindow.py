from PySide.QtGui import *
from PySide.QtCore import *
import logging
from itertools import chain
from ui import font, setTranslationLocale
from ui.customwidgets import SearchBox, SortOrderMenu
from ui.configdialog import ConfigDialog
from ui.mainwindow_ui import Ui_mainWindow
from ui.heatmap import HeatMap, cellColors
from config import settings, nikki


class MainWindow(QMainWindow, Ui_mainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.cfgDialog = self.heatMap = None  # create on on_cfgAct_triggered
        geo = settings['Main'].get('windowgeo')
        self.restoreGeometry(QByteArray.fromHex(geo))
        # setup TagList width
        tListW = settings['Main'].getint('taglistwidth', 0)
        if not self.isMaximized():
            self.splitter.setSizes([tListW, self.width()-tListW])
        # setup sort menu
        sorMenu = SortOrderMenu(self)
        sorMenu.orderChanged.connect(self.nList.sort)
        self.sorAct.setMenu(sorMenu)
        self.toolBar.widgetForAction(self.sorAct).setPopupMode(QToolButton.InstantPopup)
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
        # setup shortcuts
        searchSc = QShortcut(QKeySequence.Find, self)
        searchSc.activated.connect(self.searchBox.setFocus)
        self.addAction(self.mapAct)

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
        setTranslationLocale()
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

    @Slot()
    def on_mapAct_triggered(self):
        ratio = {QLocale.Chinese: 1, QLocale.English: 5, QLocale.Japanese: 1.2,
                 }.get(QLocale().language(), 1)
        logging.debug('HeatMap got length ratio %s' % ratio)

        def colorFunc(y, m, d):
            """Iter through model once and cache result. Return QColor used to draw cell bg."""
            data = colorFunc.cached.get((y, m, d), 0)
            if data == 0:
                return QColor(*cellColors[0])
            elif data < 200 * ratio:
                return QColor(*cellColors[1])
            elif data < 550 * ratio:
                return QColor(*cellColors[2])
            else:
                return QColor(*cellColors[3])

        colorFunc.cached = {}
        model = self.nList.originModel
        for i in range(model.rowCount()):
            dt, length = model.index(i, 1).data(), model.index(i, 6).data()
            year, month, last = dt.split('-')
            colorFunc.cached[(int(year), int(month), int(last[:2]))] = length

        try:
            self.heatMap.activateWindow()
        except (AttributeError, RuntimeError):
            self.heatMap = HeatMap(self, objectName='heatMap', font=font.date)
            self.heatMap.closeSc = QShortcut(QKeySequence(Qt.Key_Escape), self.heatMap,
                                             activated=self.heatMap.close)
            self.heatMap.setColorFunc(colorFunc)
            self.heatMap.setAttribute(Qt.WA_DeleteOnClose)
            self.heatMap.resize(self.size())
            self.heatMap.move(self.pos())
            self.heatMap.setWindowFlags(Qt.Window | Qt.WindowTitleHint)
            self.heatMap.setWindowTitle('HeatMap')
            self.heatMap.show()

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
        """Update label that display count of diaries in Main List.
        'XX diaries' format is just fine, don't use 'XX diaries,XX results'."""
        filtered = (self.nList.modelProxy.filterFixedString(0)
                    or self.nList.modelProxy.filterFixedString(1))
        c = self.nList.modelProxy.rowCount() if filtered else self.nList.originModel.rowCount()
        self.countLabel.setText(self.tr('%i diaries') % c)
