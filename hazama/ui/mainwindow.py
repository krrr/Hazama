import logging
from PySide.QtGui import *
from PySide.QtCore import *
from hazama.ui import (font, setTranslationLocale, winDwmExtendWindowFrame, scaleRatio,
                       makeQIcon, saveWidgetGeo, restoreWidgetGeo)
from hazama.ui.customwidgets import QLineEditWithMenuIcon
from hazama.ui.configdialog import ConfigDialog
from hazama.ui.mainwindow_ui import Ui_mainWindow
from hazama.ui.heatmap import HeatMap
from hazama import updater
from hazama.config import settings, isWin


class MainWindow(QMainWindow, Ui_mainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.cfgDialog = self.heatMap = None  # create on on_cfgAct_triggered
        restoreWidgetGeo(self, settings['Main'].get('windowGeo'))
        # setup toolbar bg properties; the second stage is in showEvent
        self.onExtendTitleBarBgChanged(init=True)
        self.toolBar.setIconSize(QSize(24, 24) * scaleRatio)

        # setup TagList width
        tListW = settings['Main'].getint('tagListWidth')
        tListW = tListW * scaleRatio if tListW else int(self.width() * 0.2)
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
        self.toolBar.addWidget(countLabel)

        # setup search box
        box = self.searchBox = SearchBox(self.toolBar)
        p = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        p.setHorizontalStretch(5)
        box.setSizePolicy(p)
        box.setMinimumHeight(22 * scaleRatio)
        box.setMinimumWidth(box.minimumHeight() * 7.5)
        box.contentChanged.connect(self.diaryList.setFilterBySearchString)
        self.toolBar.addWidget(box)
        spacerWidget = QWidget(self.toolBar)
        spacerWidget.setFixedSize(2.5 * scaleRatio, 1)
        self.toolBar.addWidget(spacerWidget)
        if settings['Main'].getboolean('tagListVisible'):
            self.tListAct.trigger()
        else:
            self.tagList.hide()
        # setup shortcuts
        searchSc = QShortcut(QKeySequence.Find, self)
        searchSc.activated.connect(self.searchBox.setFocus)

        # setup bigger toolbar icons
        if scaleRatio > 1.0:
            for act, fname in [(self.cfgAct, 'config'), (self.creAct, 'new'),
                               (self.delAct, 'delete'), (self.mapAct, 'heatmap'),
                               (self.sorAct, 'sort'), (self.tListAct, 'tag-list')]:
                act.setIcon(makeQIcon(':/toolbar/%s.png' % fname))

        # setup auto update check
        if updater.isCheckNeeded():
            task = updater.CheckUpdate()
            QTimer.singleShot(1200, task.start)
            task.succeeded.connect(self.setUpdateHint)  # use lambda here will cause segfault!

        # delay list loading until main event loop start
        QTimer.singleShot(0, self.diaryList.load)

    def showEvent(self, event):
        # style polished, we can get correct height of toolbar now
        self._applyExtendTitleBarBg()
        self.diaryList.setFocus()

    def closeEvent(self, event):
        settings['Main']['windowGeo'] = saveWidgetGeo(self)
        tListVisible = self.tagList.isVisible()
        settings['Main']['tagListVisible'] = str(tListVisible)
        if tListVisible:
            settings['Main']['tagListWidth'] = str(int(self.splitter.sizes()[0] / scaleRatio))
        event.accept()

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
            i.triggered[bool].connect(self.onSortOrderChanged)
        # restore from settings
        order = settings['Main']['listSortBy']
        locals()[order].setChecked(True)
        if settings['Main'].getboolean('listReverse'):
            desc.setChecked(True)
        else:
            asc.setChecked(True)
        self.sorAct.setMenu(menu)

    def retranslate(self):
        """Set translation after language changed in ConfigDialog"""
        setTranslationLocale()
        self.retranslateUi(self)
        self.searchBox.retranslate()
        self.updateCountLabel()

    def onExtendTitleBarBgChanged(self, init=False):
        # it's being called by __init__ when init is True
        ex = settings['Main'].getboolean('extendTitleBarBg')
        self.toolBar.setProperty('extendTitleBar', ex)
        type_ = ''
        if ex:
            type_ = 'win' if isWin else 'other'
        self.toolBar.setProperty('titleBarBgType', type_)
        if not init:
            self.style().unpolish(self)
            self.style().polish(self)
            self._applyExtendTitleBarBg()

    def _applyExtendTitleBarBg(self):
        if isWin and settings['Main'].getboolean('extendTitleBarBg'):
            winDwmExtendWindowFrame(self.winId(), self.toolBar.height())
            self.setAttribute(Qt.WA_TranslucentBackground)

    def onSortOrderChanged(self, checked):
        name = self.sender().name
        if name in ['asc', 'desc']:
            settings['Main']['listReverse'] = str(name == 'desc')
        elif checked:
            settings['Main']['listSortBy'] = name
        self.diaryList.sort()

    def toggleTagList(self, checked):
        self.tagList.setVisible(checked)
        if checked:
            self.tagList.load()
        else:
            self.diaryList.setFilterByTag('')
            self.tagList.clear()
            settings['Main']['tagListWidth'] = str(int(self.splitter.sizes()[0] / scaleRatio))

    def updateCountLabel(self):
        """Update label that display count of diaries in Main List.
        'XX diaries' format is just fine, don't use 'XX diaries,XX results'."""
        filtered = (self.diaryList.modelProxy.filterPattern(0) or
                    self.diaryList.modelProxy.filterPattern(1))
        m = self.diaryList.modelProxy if filtered else self.diaryList.originModel
        self.countLabel.setText(self.tr('%i diaries') % m.rowCount())

    def updateCountLabelOnLoad(self):
        self.countLabel.setText(self.tr('loading...'))

    def setUpdateHint(self, enabled=None):
        if enabled is None:
            enabled = bool(updater.foundUpdate)

        if enabled:
            ico = self.cfgAct.icon()
            self.cfgAct.originIcon = QIcon(ico)  # save copy
            sz = QSize(24, 24) * scaleRatio
            origin = ico.pixmap(sz)
            painter = QPainter(origin)
            painter.drawPixmap(0, 0, QPixmap(':/toolbar/update-mark.png').scaled(sz))
            painter.end()  # this should be called at destruction, but... critical error everywhere?
            ico.addPixmap(origin)
            self.cfgAct.setIcon(ico)
        elif hasattr(self.cfgAct, 'originIcon'):
            self.cfgAct.setIcon(self.cfgAct.originIcon)
            del self.cfgAct.originIcon

    @Slot()
    def on_cfgAct_triggered(self):
        """Start config dialog"""
        try:
            self.cfgDialog.activateWindow()
        except (AttributeError, RuntimeError):
            self.cfgDialog = ConfigDialog(self)
            self.cfgDialog.langChanged.connect(self.retranslate)
            self.cfgDialog.bkRestored.connect(self.diaryList.reload)
            self.cfgDialog.accepted.connect(self.diaryList.setDelegateOfTheme)
            self.cfgDialog.accepted.connect(self.tagList.setDelegateOfTheme)
            self.cfgDialog.extendBgChanged.connect(self.onExtendTitleBarBgChanged)
            self.cfgDialog.show()

    @Slot()
    def on_mapAct_triggered(self):
        # ratios are from http://www.sonasphere.com/blog/?p=1319
        ratio = {QLocale.Chinese: 1, QLocale.English: 4, QLocale.Japanese: 1.5,
                 }.get(QLocale().language(), 1.6)
        logging.debug('HeatMap got length ratio %s' % ratio)
        ds = ['0', '< %d' % (200 * ratio), '< %d' % (550 * ratio),
              '>= %d' % (550 * ratio)]
        descriptions = [i + ' ' + qApp.translate('HeatMap', '(characters)') for i in ds]

        def colorFunc(y, m, d, cellColors):
            data = colorFunc.cached.get((y, m, d), 0)
            if data == 0:
                return cellColors[0]
            elif data < 200 * ratio:
                return cellColors[1]
            elif data < 550 * ratio:
                return cellColors[2]
            else:
                return cellColors[3]

        # iter through model once and cache result.
        colorFunc.cached = {}
        model = self.diaryList.originModel
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
            self.heatMap.sample.setDescriptions(descriptions)
            self.heatMap.setAttribute(Qt.WA_DeleteOnClose)
            self.heatMap.resize(self.size())
            self.heatMap.move(self.pos())
            self.heatMap.setWindowFlags(Qt.Window | Qt.WindowTitleHint)
            self.heatMap.setWindowTitle('HeatMap')
            self.heatMap.move(self.pos() + QPoint(12, 12)*scaleRatio)
            self.heatMap.show()


class SearchBox(QLineEditWithMenuIcon):
    """The real-time search box in toolbar. contentChanged signal will be
    delayed after textChanged, it prevent lagging when text changing quickly
    and the amount of data is large."""
    contentChanged = Signal(str)  # replace textChanged

    def __init__(self, parent=None):
        super().__init__(parent, objectName='searchBox')

        self.button = QToolButton(self, objectName='searchBoxBtn')
        sz = QSize(16, 16) * scaleRatio
        self.button.setFocusPolicy(Qt.NoFocus)
        self.button.setFixedSize(sz)
        self.button.setIconSize(sz)
        self.button.setCursor(Qt.ArrowCursor)
        self.button.clicked.connect(self.clear)
        clearSc = QShortcut(QKeySequence(Qt.Key_Escape), self)
        clearSc.activated.connect(self.clear)
        self.textChanged.connect(self._updateIco)
        self.retranslate()
        self.setMinimumHeight(int(self.button.height() * 1.2))
        self.setTextMargins(QMargins(2, 0, sz.width(), 0))

        self._isTextBefore = True
        self._searchIco = makeQIcon(':/search.png', scaled2x=True)
        self._clrIco = makeQIcon(':/search-clr.png', scaled2x=True)
        self._updateIco('')  # initialize the icon

        self._delay = QTimer(self)
        self._delay.setSingleShot(True)
        self._delay.setInterval(310)
        self._delay.timeout.connect(lambda: self.contentChanged.emit(self.text()))
        self.textChanged.connect(self._updateDelayTimer)

    def resizeEvent(self, event):
        w, h = event.size().toTuple()
        pos_y = (h - self.button.height()) / 2
        self.button.move(w - self.button.width() - pos_y, pos_y)

    def _updateDelayTimer(self, s):
        if s == '':  # fast clear
            self._delay.stop()
            self.contentChanged.emit(self.text())
        else:
            self._delay.start()  # restart if already started

    def _updateIco(self, text):
        """Update button icon"""
        if self._isTextBefore == bool(text): return
        self.button.setIcon(self._clrIco if text else self._searchIco)
        self._isTextBefore = bool(text)

    def retranslate(self):
        self.setPlaceholderText(self.tr('Search'))
