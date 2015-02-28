from PySide.QtGui import *
from PySide.QtCore import *
import logging
from itertools import chain
from ui import font, setTranslationLocale
from ui.customwidgets import QLineEditWithMenuIcon
from ui.configdialog import ConfigDialog
from ui.mainwindow_ui import Ui_mainWindow
from ui.heatmap import HeatMap, cellColors
from config import settings, nikki, saveSettings


class MainWindow(QMainWindow, Ui_mainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.cfgDialog = self.heatMap = None  # create on on_cfgAct_triggered
        geo = settings['Main'].get('windowGeo')
        self.restoreGeometry(QByteArray.fromHex(geo))
        # setup TagList width
        tListW = settings['Main'].getint('tagListWidth', 0)
        if not self.isMaximized():
            self.splitter.setSizes([tListW, self.width()-tListW])
        # setup sort menu
        self.createSortMenu()
        self.toolBar.widgetForAction(self.sorAct).setPopupMode(QToolButton.InstantPopup)
        # Qt Designer doesn't allow us to add widget in toolbar
        # setup count label
        countLabel = self.countLabel = QLabel(self.toolBar)
        countLabel.setObjectName('countLabel')
        p = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        p.setHorizontalStretch(8)
        countLabel.setSizePolicy(p)
        countLabel.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        countLabel.setIndent(6)
        self.updateCountLabel()
        self.toolBar.addWidget(countLabel)
        # setup search box
        searchBox = self.searchBox = SearchBox(self.toolBar)
        p = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        p.setHorizontalStretch(5)
        searchBox.setSizePolicy(p)
        searchBox.setMinimumWidth(searchBox.sizeHint().height() * 8)
        searchBox.textChanged.connect(self.nList.setFilterBySearchString)
        self.toolBar.addWidget(searchBox)
        if settings['Main'].getboolean('tagListVisible'):
            self.tListAct.trigger()
        else:
            self.tList.hide()
        # setup shortcuts
        searchSc = QShortcut(QKeySequence.Find, self)
        searchSc.activated.connect(self.searchBox.setFocus)
        self.addAction(self.mapAct)

    def createSortMenu(self):
        """Add sort order menu to sorAct."""
        menu = QMenu(self)
        group = QActionGroup(menu)
        datetime = QAction(self.tr('Date'), group)
        datetime.name = 'datetime'
        title = QAction(self.tr('Title'), group)
        title.name = 'title'
        length = QAction(self.tr('Length'), group)
        length.name = 'length'
        ascDescGroup = QActionGroup(menu)
        asc = QAction(self.tr('Ascending'), ascDescGroup)
        asc.name = 'asc'
        desc = QAction(self.tr('Descending'), ascDescGroup)
        desc.name = 'desc'
        for i in [datetime, title, length, None, asc, desc]:
            if i is None:
                menu.addSeparator()
                continue
            i.setCheckable(True)
            menu.addAction(i)
            i.triggered[bool].connect(self.sortOrderChanged)
        # restore from settings
        order = settings['Main'].get('listSortBy', 'datetime')
        locals()[order].setChecked(True)
        if settings['Main'].getboolean('listReverse', True):
            desc.setChecked(True)
        else:
            asc.setChecked(True)
        self.sorAct.setMenu(menu)

    def closeEvent(self, event):
        settings['Main']['windowGeo'] = str(self.saveGeometry().toHex())
        tListVisible = self.tList.isVisible()
        settings['Main']['tagListVisible'] = str(tListVisible)
        if tListVisible:
            settings['Main']['tagListWidth'] = str(self.splitter.sizes()[0])
        saveSettings()
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
            self.heatMap = HeatMap(self, objectName='heatMap', font=font.datetime)
            self.heatMap.closeSc = QShortcut(QKeySequence(Qt.Key_Escape), self.heatMap,
                                             activated=self.heatMap.close)
            self.heatMap.setColorFunc(colorFunc)
            self.heatMap.setAttribute(Qt.WA_DeleteOnClose)
            self.heatMap.resize(self.size())
            self.heatMap.move(self.pos())
            self.heatMap.setWindowFlags(Qt.Window | Qt.WindowTitleHint)
            self.heatMap.setWindowTitle('HeatMap')
            self.heatMap.show()

    def sortOrderChanged(self, checked):
        name = self.sender().name
        if name in ['asc', 'desc']:
            settings['Main']['listReverse'] = str(name == 'desc')
        elif checked:
            settings['Main']['listSortBy'] = name
        self.nList.sort()

    def toggleTagList(self, checked):
        self.tList.setVisible(checked)
        if checked:
            self.tList.load()
        else:
            self.nList.setFilterByTag('')
            self.tList.clear()
            settings['Main']['tagListWidth'] = str(self.splitter.sizes()[0])

    def showEvent(self, event):
        self.nList.setFocus()

    def updateCountLabel(self):
        """Update label that display count of diaries in Main List.
        'XX diaries' format is just fine, don't use 'XX diaries,XX results'."""
        filtered = (self.nList.modelProxy.filterPattern(0)
                    or self.nList.modelProxy.filterPattern(1))
        c = self.nList.modelProxy.rowCount() if filtered else self.nList.originModel.rowCount()
        self.countLabel.setText(self.tr('%i diaries') % c)


class SearchBox(QLineEditWithMenuIcon):
    """The real-time search box in toolbar"""
    def __init__(self, parent=None):
        super(SearchBox, self).__init__(parent, objectName='searchBox')
        self.setMinimumHeight(23)  # looks fine when toolbar icon is 24x24
        self.setTextMargins(QMargins(2, 0, 20, 0))
        self.button = QToolButton(self, objectName='searchBoxBtn')
        self.button.setFocusPolicy(Qt.NoFocus)
        self.button.setFixedSize(18, 18)
        self.button.setCursor(Qt.ArrowCursor)
        self.button.clicked.connect(self.clear)
        clearSc = QShortcut(QKeySequence(Qt.Key_Escape), self)
        clearSc.activated.connect(self.clear)
        self.textChanged.connect(self._updateIco)
        self.retranslate()
        self.isTextBefore = True
        self._updateIco('')  # initiallize the icon

    def resizeEvent(self, event):
        w, h = event.size().toTuple()
        pos_y = (h - 18) / 2
        self.button.move(w - 18 - pos_y, pos_y)

    def _updateIco(self, text):
        """Update button icon"""
        if self.isTextBefore == bool(text): return
        ico_name = 'search_clr' if text else 'search'
        self.button.setIcon(QIcon(':/images/%s.png' % ico_name))
        self.isTextBefore = bool(text)

    def retranslate(self):
        self.setPlaceholderText(self.tr('Search'))
