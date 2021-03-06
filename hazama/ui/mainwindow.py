import os
import logging
import PySide.QtCore
from collections import OrderedDict
from PySide.QtGui import *
from PySide.QtCore import *
from hazama.ui.editor import Editor
from hazama.ui import (font, winDwmExtendWindowFrame, scaleRatio, refreshStyle,
                       makeQIcon, saveWidgetGeo, restoreWidgetGeo, markIcon)
from hazama.ui.customwidgets import QLineEditWithMenuIcon
from hazama.ui.customobjects import NGraphicsDropShadowEffect
from hazama.ui.diarymodel import DiaryModel
from hazama.ui.configdialog import ConfigDialog, StyleSheetEditor
from hazama.ui.mainwindow_ui import Ui_mainWindow
from hazama.ui.heatmap import HeatMap
from hazama import updater, mactype
from hazama.config import settings, db, isWin, winVer, isWin10, isWin7, isWin8


class MainWindow(QMainWindow, Ui_mainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.cfgDialog = self.heatMap = self.ssEditor = None  # create on action triggered
        self.editors = OrderedDict()  # diaryId => Editor, id of new diary is -1

        restoreWidgetGeo(self, settings['Main'].get('windowGeo'))
        # setup toolbar bg properties; the second stage is in showEvent
        self.setToolbarProperty()
        self.toolBar.setIconSize(QSize(24, 24) * scaleRatio)

        self.diaryList.editAct.triggered.connect(self.startEditor)
        self.diaryList.gotoAct.triggered.connect(self.onGotoActTriggered)
        self.diaryList.delAct.triggered.connect(self.deleteDiary)

        # setup TagList
        self._tagListAni = QPropertyAnimation(self, 'tagListWidth')
        self._tagListAni.setEasingCurve(QEasingCurve(QEasingCurve.OutCubic))
        self._tagListAni.setDuration(150)
        self._tagListAni.finished.connect(self.onTagListAniFinished)

        # setup sort menu
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
        self.toolBar.widgetForAction(self.sorAct).setPopupMode(QToolButton.InstantPopup)

        # setup count label
        # Qt Designer doesn't allow us to add widget in toolbar
        p = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        p.setHorizontalStretch(8)
        spacer1 = QWidget(self.toolBar)
        spacer1.setSizePolicy(p)
        self.toolBar.addWidget(spacer1)
        countLabel = self.countLabel = QLabel(self.toolBar, objectName='countLabel')
        countLabel.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))
        countLabel.setMargin(4 * scaleRatio)
        self.toolBar.addWidget(countLabel)

        # setup search box
        box = self.searchBox = SearchBox(self)
        p = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        p.setHorizontalStretch(5)
        box.setSizePolicy(p)
        box.setMinimumHeight(22 * scaleRatio)
        box.setMinimumWidth(box.minimumHeight() * 7.5)
        box.byTitleTextAct.triggered.connect(self._setSearchBy)
        box.byDatetimeAct.triggered.connect(self._setSearchBy)
        self._setSearchBy()
        self.toolBar.addWidget(box)
        spacer2 = QWidget(self.toolBar)
        spacer2.setFixedSize(2.5 * scaleRatio, 1)
        self.toolBar.addWidget(spacer2)
        if settings['Main'].getboolean('tagListVisible'):
            self.tListAct.setChecked(True)  # will not trigger signal
            if self.isMaximized():
                # Qt will maximize the window after showing... why?
                QTimer.singleShot(0, lambda: self.toggleTagList(True, animated=False))
            else:
                self.toggleTagList(True, animated=False)
        else:
            self.tagList.hide()  # don't use toggleTagList, it will save width
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
            settings['Main']['tagListWidth'] = str(int(self._tagListWidth() / scaleRatio))

    def changeEvent(self, event):
        if event.type() != QEvent.LanguageChange:
            return super().changeEvent(event)

        self.retranslateUi(self)
        self.searchBox.retranslate()
        self.updateCountLabel()
        self.tagList.reload()  # "All" item

    def contextMenuEvent(self, event):
        """Hidden menu."""
        menu = QMenu()
        menu.addAction(QAction(self.tr('Edit Style Sheet'), menu, triggered=self.startStyleSheetEditor))
        menu.addAction(QAction(self.tr('Open Data Directory'), menu,
                               triggered=lambda: QDesktopServices.openUrl('file:///' + os.getcwd())))
        if mactype.isEnabled():
            menu.addAction(QAction(self.tr('Open MacType Config'), menu,
                                   triggered=lambda: QDesktopServices.openUrl('file:///' + mactype.configPath)))
        menu.addAction(QAction(self.tr('About Qt'), menu, triggered=qApp.aboutQt))

        menu.exec_(event.globalPos())
        menu.deleteLater()

    # disable winEvent hack if PySide version doesn't support it
    if hasattr(PySide.QtCore, 'MSG') and hasattr(MSG, 'lParam'):
        def winEvent(self, msg):
            """Make extended frame draggable (Windows only). This hack is better than
            receiving MouseMoveEvent and moving the window because it can handle aero snap."""
            if msg.message == 0x0084:  # WM_NCHITTEST
                pos = QPoint(msg.lParam & 0xFFFF, msg.lParam >> 16)
                widget = self.childAt(self.mapFromGlobal(pos))
                if widget is self.toolBar or widget is self.countLabel:
                    # qApp.mouseButtons() & Qt.LeftButton doesn't work here; must use win32api
                    return True, 2  # HTCAPTION
                else:
                    return False, 0
            else:
                return False, 0  # let Qt handle the message

    def _tagListWidth(self):
        return self.splitter.sizes()[0]

    def _setTagListWidth(self, w):
        sizes = self.splitter.sizes()
        if sizes[1] == 0:
            self.splitter.setSizes([w, self.width()-w])
        else:
            sizes[1] = sizes[0] + sizes[1] - w
            sizes[0] = w
            self.splitter.setSizes(sizes)

    def startStyleSheetEditor(self):
        try:
            self.ssEditor.activateWindow()
        except (AttributeError, RuntimeError):
            self.ssEditor = StyleSheetEditor(self)
            self.ssEditor.appearanceChanged.connect(self.onAppearanceChanged)
            self.ssEditor.resize(QSize(600, 550) * scaleRatio)
            self.ssEditor.show()

    def setToolbarProperty(self):
        ex = settings['Main'].getboolean('extendTitleBarBg')
        self.toolBar.setProperty('extendTitleBar', ex)
        type_ = ''
        if ex:
            if isWin10:
                type_ = 'win10'  # system theme has no border
            elif isWin:
                type_ = 'win'
            else:
                type_ = 'other'
        self.toolBar.setProperty('titleBarBgType', type_)
        if self.isVisible():  # not being called by __init__
            refreshStyle(self.toolBar)
            refreshStyle(self.countLabel)  # why is this necessary?
            self._applyExtendTitleBarBg()

    def _applyExtendTitleBarBg(self):
        if settings['Main'].getboolean('extendTitleBarBg'):
            if isWin:
                winDwmExtendWindowFrame(self.winId(), top=self.toolBar.height())
                self.setAttribute(Qt.WA_TranslucentBackground)

            if not isWin or not isWin8:
                eff = NGraphicsDropShadowEffect(5 if isWin7 else 3, self.countLabel)
                eff.setColor(QColor(Qt.white))
                eff.setOffset(0, 0)
                eff.setBlurRadius((16 if isWin7 else 8) * scaleRatio)
                self.countLabel.setGraphicsEffect(eff)
        else:
            self.countLabel.setGraphicsEffect(None)

    def onSortOrderChanged(self, checked):
        name = self.sender().name
        if name in ['asc', 'desc']:
            settings['Main']['listReverse'] = str(name == 'desc')
        elif checked:
            settings['Main']['listSortBy'] = name
        self.diaryList.sort()

    def toggleTagList(self, show, animated=True):
        if show:
            if self._tagListAni.state() == QAbstractAnimation.Running:
                self._tagListAni.stop()
            else:
                self.tagList.load()
                self.tagList.show()
            # minus 1 to make animation direction check correct
            tListW = settings['Main'].getint('tagListWidth')
            tListW = tListW * scaleRatio if tListW else int(self.width() * 0.2)
            if animated:
                self._tagListAni.hiding = False
                self._tagListAni.setStartValue(max(self._tagListWidth(),
                                                   self.tagList.minimumSize().width()))
                self._tagListAni.setEndValue(tListW)
                self._tagListAni.start()
            else:
                self._setTagListWidth(tListW)
        else:
            if self._tagListAni.state() == QAbstractAnimation.Running:
                self._tagListAni.stop()
            else:
                settings['Main']['tagListWidth'] = str(int(self._tagListWidth() / scaleRatio))
            if animated:
                self._tagListAni.hiding = True
                self._tagListAni.setStartValue(self._tagListWidth())
                self._tagListAni.setEndValue(self.tagList.minimumSize().width())
                self._tagListAni.start()
            else:
                self.tagList.hide()

    def updateCountLabel(self):
        """Update label that display count of diaries in Main List.
        'XX diaries' format is just fine, don't use 'XX diaries,XX results'."""
        self.countLabel.setText(self.tr('%i diaries') %
                                self.diaryList.modelProxy.rowCount())

    def updateCountLabelOnLoad(self):
        self.countLabel.setText(self.tr('loading...'))

    def setUpdateHint(self, enabled=None):
        if enabled is None:
            enabled = bool(updater.foundUpdate)

        if enabled:
            ico = self.cfgAct.icon()
            self.cfgAct.originIcon = QIcon(ico)  # save copy
            self.cfgAct.setIcon(markIcon(ico, QSize(24, 24)), ':/toolbar/update-mark.png')
        elif hasattr(self.cfgAct, 'originIcon'):
            self.cfgAct.setIcon(self.cfgAct.originIcon)
            del self.cfgAct.originIcon

    def _setSearchBy(self):
        sen = self.sender()
        if sen:
            self.searchBox.contentChanged.disconnect()
        if sen == self.searchBox.byTitleTextAct or sen is None:
            self.searchBox.contentChanged.connect(self.diaryList.setFilterBySearchString)
        else:
            self.searchBox.contentChanged.connect(self.diaryList.setFilterByDatetime)

    def deleteDiary(self):
        indexes = self.diaryList.selectedIndexes()
        if not indexes:
            return
        msg = QMessageBox(self)
        okBtn = msg.addButton(qApp.translate('Dialog', 'Delete'), QMessageBox.AcceptRole)
        msg.setIcon(QMessageBox.Question)
        msg.addButton(qApp.translate('Dialog', 'Cancel'), QMessageBox.RejectRole)
        msg.setWindowTitle(self.tr('Delete diaries'))
        msg.setText(self.tr('Selected diaries will be deleted permanently!'))
        msg.exec_()
        msg.deleteLater()

        if msg.clickedButton() == okBtn:
            for i in indexes: db.delete(i.data())
            for r in reversed(sorted(i.row() for i in indexes)):
                self.diaryList.model().removeRow(r)
            self.tagList.reload()  # tags might changed

    def startEditor(self, idx=None):
        dic = self.diaryList.getDiaryDict(idx or self.diaryList.currentIndex())
        id_ = dic['id']
        if id_ in self.editors:
            self.editors[id_].activateWindow()
        else:
            e = Editor(dic)
            self._setEditorStaggerPos(e)
            self.editors[id_] = e
            e.closed.connect(self.onEditorClose)
            pre, next_ = lambda: self._editorMove(-1), lambda: self._editorMove(1)
            e.preSc.activated.connect(pre)
            e.quickPreSc.activated.connect(pre)
            e.nextSc.activated.connect(next_)
            e.quickNextSc.activated.connect(next_)
            e.show()

    def startEditorNew(self):
        if -1 in self.editors:
            self.editors[-1].activateWindow()
        else:
            e = Editor({'id': -1})
            self._setEditorStaggerPos(e)
            self.editors[-1] = e
            e.closed.connect(self.onEditorClose)
            e.show()

    def _setEditorStaggerPos(self, editor):
        if self.editors:
            lastOpenEditor = list(self.editors.values())[-1]
            pos = lastOpenEditor.pos() + QPoint(16, 16) * scaleRatio
            # can't check available screen space because of bug in pyside
            editor.move(pos)

    def _editorMove(self, step):
        if len(self.editors) > 1: return
        id_ = list(self.editors.keys())[0]
        editor = self.editors[id_]
        if editor.needSave(): return

        model = self.diaryList.modelProxy
        idx = model.match(model.index(0, 0), 0, id_, flags=Qt.MatchExactly)
        if len(idx) != 1: return
        row = idx[0].row()  # the row of the caller (Editor) 's diary in proxy model

        if ((step == -1 and row == 0) or
           (step == 1 and row == model.rowCount() - 1)):
            return
        newIdx = model.index(row+step, 0)
        self.diaryList.clearSelection()
        self.diaryList.setCurrentIndex(newIdx)
        dic = self.diaryList.getDiaryDict(newIdx)
        editor.fromDiaryDict(dic)
        self.editors[dic['id']] = self.editors.pop(id_)

    def onEditorClose(self, id_, needSave):
        """Write editor's data to model and database, and destroy editor"""
        editor = self.editors[id_]
        new = id_ == -1
        if needSave:
            qApp.setOverrideCursor(QCursor(Qt.WaitCursor))
            dic = editor.toDiaryDict()
            if not new and not editor.tagModified:  # let database skip heavy tag update operation
                dic['tags'] = None
            row = self.diaryList.originModel.saveDiary(dic)

            self.diaryList.clearSelection()
            self.diaryList.setCurrentIndex(self.diaryList.modelProxy.mapFromSource(
                self.diaryList.originModel.index(row, 0)))

            if new:
                self.updateCountLabel()
            if editor.tagModified:
                self.tagList.reload()
            qApp.restoreOverrideCursor()
        editor.deleteLater()
        del self.editors[id_]

    def onAppearanceChanged(self):
        self.diaryList.setupTheme()
        self.tagList.setupTheme()
        self.setToolbarProperty()

    def onGotoActTriggered(self):
        """Scroll the list to the original position (unfiltered) of an entry."""
        if self.searchBox.text():
            self.searchBox.clear()
        if self.tagList.selectedIndexes():
            self.tagList.setCurrentRow(0)
        self.diaryList.scrollTo(self.diaryList.currentIndex(), QListView.PositionAtCenter)

    def onTagListAniFinished(self):
        if self._tagListAni.hiding:
            self.tagList.hide()
            self.tagList.clear()

    @Slot()
    def on_cfgAct_triggered(self):
        """Start config dialog"""
        try:
            self.cfgDialog.activateWindow()
        except (AttributeError, RuntimeError):
            self.cfgDialog = ConfigDialog(self)
            self.cfgDialog.diaryChanged.connect(self.diaryList.reload)
            self.cfgDialog.appearanceChanged.connect(self.onAppearanceChanged)
            self.cfgDialog.show()

    @Slot()
    def on_mapAct_triggered(self):
        # some languages have more info in single character
        # ratios are from http://www.sonasphere.com/blog/?p=1319
        ratio = {QLocale.Chinese: 1, QLocale.English: 4, QLocale.Japanese: 1.5,
                 }.get(QLocale().language(), 1.6)
        logging.debug('HeatMap got length ratio %s' % ratio)
        ds = ['0', '< %d' % (200 * ratio), '< %d' % (550 * ratio),
              '>= %d' % (550 * ratio)]
        descriptions = [i + ' ' + qApp.translate('HeatMap', '(characters)') for i in ds]

        def colorFunc(data, cellColors):
            if data == 0:
                return cellColors[0]
            elif data < 200 * ratio:
                return cellColors[1]
            elif data < 550 * ratio:
                return cellColors[2]
            else:
                return cellColors[3]

        # iter through model once and cache result.
        cached = {}
        for diary in self.diaryList.originModel.getAll():
            dt, length = diary[DiaryModel.DATETIME], diary[DiaryModel.LENGTH]
            year, month, last = dt.split('-')
            cached[(int(year), int(month), int(last[:2]))] = length

        try:
            self.heatMap.activateWindow()
        except (AttributeError, RuntimeError):
            self.heatMap = HeatMap(self, objectName='heatMap', font=font.datetime)
            self.heatMap.closeSc = QShortcut(QKeySequence(Qt.Key_Escape), self.heatMap,
                                             activated=self.heatMap.close)
            self.heatMap.setColorFunc(colorFunc)
            self.heatMap.setDataFunc(lambda y, m, d: cached.get((y, m, d), 0))
            self.heatMap.sample.setDescriptions(descriptions)
            self.heatMap.setAttribute(Qt.WA_DeleteOnClose)
            self.heatMap.resize(self.size())
            self.heatMap.setWindowFlags(Qt.Window | Qt.WindowTitleHint)
            self.heatMap.setWindowTitle(self.tr('Heat Map'))
            self.heatMap.move(self.pos() + QPoint(12, 12)*scaleRatio)
            self.heatMap.show()

    tagListWidth = Property(int, _tagListWidth, _setTagListWidth)


class SearchBox(QLineEditWithMenuIcon):
    """The real-time search box in toolbar. contentChanged signal will be
    delayed after textChanged, it prevent lagging when text changing quickly
    and the amount of data is large."""
    contentChanged = Signal(str)  # replace textChanged

    def __init__(self, parent=None):
        super().__init__(parent, objectName='searchBox')
        self._searchByTip = None

        self.btn = QPushButton(self, objectName='searchBoxBtn')
        sz = QSize(16, 16) * scaleRatio
        self.btn.setFocusPolicy(Qt.NoFocus)
        self.btn.setFixedSize(sz)
        self.btn.setIconSize(sz)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(self.onBtnClicked)

        self._byMenu = menu = QMenu(self)
        group = QActionGroup(menu)
        self.byTitleTextAct = QAction(self.tr('Title && Text'), group)
        self.byDatetimeAct = QAction(self.tr('Date (YYYY-MM-DD)'), group)
        for i in (self.byTitleTextAct, self.byDatetimeAct):
            i.setCheckable(True)
            menu.addAction(i)
        self.byTitleTextAct.setChecked(True)

        clearSc = QShortcut(QKeySequence(Qt.Key_Escape), self)
        clearSc.activated.connect(self.clear)
        self.textChanged.connect(self.onTextChanged)
        self.retranslate()
        self.setMinimumHeight(int(self.btn.height() * 1.2))
        self.setTextMargins(QMargins(2, 0, sz.width(), 0))

        self._hasText = True
        self._searchIco = makeQIcon(':/search.png', scaled2x=True)
        self._clrIco = makeQIcon(':/search-clr.png', scaled2x=True)
        self.onTextChanged('')  # initialize the icon

        self._delayed = QTimer(self)
        self._delayed.setSingleShot(True)
        self._delayed.setInterval(310)
        self._delayed.timeout.connect(lambda: self.contentChanged.emit(self.text()))
        self.textChanged.connect(self._updateDelayedTimer)

    def resizeEvent(self, event):
        w, h = event.size().toTuple()
        pos_y = (h - self.btn.height()) / 2
        self.btn.move(w - self.btn.width() - pos_y, pos_y)

    def retranslate(self):
        self._searchByTip = self.tr('Click to change search option')
        self.setPlaceholderText(self.tr('Search'))

    def _updateDelayedTimer(self, s):
        if s == '':  # fast clear
            self._delayed.stop()
            self._delayed.timeout.emit()  # delay this call is not a good idea
        else:
            self._delayed.start()  # restart if already started

    def onTextChanged(self, text):
        if self._hasText == bool(text): return
        self.btn.setIcon(self._clrIco if text else self._searchIco)
        self.btn.setToolTip('' if text else self._searchByTip)
        self._hasText = bool(text)

    def onBtnClicked(self):
        if self._hasText:
            self.clear()
        else:
            self._byMenu.exec_(self.btn.mapToGlobal(QPoint(0, self.btn.height())))
