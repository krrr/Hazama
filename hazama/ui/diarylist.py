import random
from PySide.QtGui import *
from PySide.QtCore import *
from hazama.ui import (font, datetimeTrans, scaleRatio, makeQIcon, refreshStyle,
                       NProperty)
from hazama.ui.diarymodel import DiaryModel
from hazama.ui.customobjects import NTextDocument, MultiSortFilterProxyModel
from hazama.ui.customwidgets import NElideLabel, MultiLineElideLabel
from hazama.config import settings, db


class DiaryListDelegate(QStyledItemDelegate):
    """ItemDelegate of old theme 'one-pixel-rect' for DiaryList, Using 'traditional'
    painting method compared to colorful theme."""
    def __init__(self):
        super().__init__()  # don't pass parent because of mem problem
        # Because some fonts have much more space at top and bottom, we use ascent instead
        # of height, and add it with a small number.
        magic = int(4 * scaleRatio)
        self.title_h = max(font.title_m.ascent(), font.datetime_m.ascent()) + magic
        self.titleArea_h = self.title_h + 4
        self.text_h = font.text_m.lineSpacing() * settings['Main'].getint('previewLines')
        self.tagPath_h = font.default_m.ascent() + magic
        self.tag_h = self.tagPath_h + 4
        self.dt_w = font.datetime_m.width(datetimeTrans('2000-01-01 00:00')) + 40
        self.all_h = None  # updated in sizeHint before each item being painting
        # doc is used to draw text(diary's body)
        self.doc = NTextDocument()
        self.doc.setDefaultFont(font.text)
        self.doc.setUndoRedoEnabled(False)
        self.doc.setDocumentMargin(0)
        self.doc.documentLayout().setPaintDevice(qApp.desktop())  # refer actual list will cause segfault
        # setup colors
        self.c_text = Qt.black
        self.c_bg = QColor(255, 236, 176)
        self.c_border = QColor(214, 172, 41)
        self.c_inActBg = QColor(255, 236, 176, 40)
        self.c_gray = QColor(93, 73, 57)

    def paint(self, painter, option, index):
        x, y, w = option.rect.x(), option.rect.y(), option.rect.width()-1
        row = index.row()
        dt, text, title, tags, formats = (index.sibling(row, i).data()
                                          for i in range(1, 6))
        selected = bool(option.state & QStyle.State_Selected)
        active = bool(option.state & QStyle.State_Active)
        # draw border and background
        painter.setPen(self.c_border)
        painter.setBrush(self.c_bg if selected and active else
                         self.c_inActBg)
        painter.drawRect(x+1, y, w-2, self.all_h)  # outer border
        if selected:  # draw inner border
            pen = QPen()
            pen.setStyle(Qt.DashLine)
            pen.setColor(self.c_gray)
            painter.setPen(pen)
            painter.drawRect(x+2, y+1, w-4, self.all_h-2)
        # draw datetime and title
        painter.setPen(self.c_gray)
        painter.drawLine(x+10, y+self.titleArea_h, x+w-10, y+self.titleArea_h)
        painter.setPen(self.c_text)
        painter.setFont(font.datetime)
        painter.drawText(x+14, y+self.titleArea_h-self.title_h, self.dt_w, self.title_h,
                         Qt.AlignVCenter, datetimeTrans(dt))
        if title:
            painter.setFont(font.title)
            title_w = w - self.dt_w - 13
            title = font.title_m.elidedText(title, Qt.ElideRight, title_w)
            painter.drawText(x+self.dt_w, y+self.titleArea_h-self.title_h, title_w, self.title_h,
                             Qt.AlignVCenter | Qt.AlignRight, title)
        # draw text
        self.doc.setText(text, formats)
        self.doc.setTextWidth(w-26)
        painter.translate(x+14, y+self.titleArea_h+2)
        self.doc.drawContentsColor(painter, QRect(0, 0, w-26, self.text_h), self.c_text)
        painter.resetTransform()
        # draw tags
        if tags:
            painter.setPen(self.c_gray)
            painter.setFont(font.default)
            painter.translate(x + 15, y+self.titleArea_h+6+self.text_h)
            real_x, max_x = x+15, w-10
            for t in tags.split():
                oneTag_w = font.default_m.width(t) + 4
                real_x += oneTag_w + 15
                if real_x > max_x: break
                tagPath = QPainterPath()
                tagPath.moveTo(8, 0)
                tagPath.lineTo(8+oneTag_w, 0)
                tagPath.lineTo(8+oneTag_w, self.tagPath_h)
                tagPath.lineTo(8, self.tagPath_h)
                tagPath.lineTo(0, self.tagPath_h/2)
                tagPath.closeSubpath()
                painter.drawPath(tagPath)
                painter.drawText(8, 0, oneTag_w, self.tagPath_h, Qt.AlignCenter, t)
                painter.translate(oneTag_w+15, 0)  # translate by offset
            else:
                painter.resetTransform()
                return
            # draw ellipsis if too many tags
            painter.setPen(Qt.DotLine)
            painter.drawLine(-4, self.tagPath_h/2, 2, self.tagPath_h/2)
            painter.resetTransform()

    def sizeHint(self, option, index):
        tag_h = self.tag_h if index.sibling(index.row(), 4).data() else 0
        self.all_h = self.titleArea_h + 2 + self.text_h + tag_h + 6
        return QSize(-1, self.all_h+3)  # 3 is spacing between entries


class DiaryListDelegateColorful(QItemDelegate):
    """ItemDelegate of theme 'colorful' for DiaryList. Using widget rendering."""
    class ItemWidget(QFrame):
        """Widget that used to draw an item in ItemDelegate.paint method.
        This widget's height is 'fixed'(two possible height) because delegate's
        sizeHint method is called very often. So font fallback will cause problem.
        """
        def __init__(self, parent=None):
            super().__init__(parent, objectName='DiaryListItem')
            self.heightWithTag = self.heightNoTag = None

            self.title = NElideLabel(self, objectName='DiaryListItemTitle')
            self.title.setFont(font.title)
            self.title.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.datetime = QLabel(self, objectName='DiaryListItemDt')
            self.datetime.setFont(font.datetime)
            self.datetime.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

            self.text = MultiLineElideLabel(self, objectName='DiaryListItemText')
            self.text.setMaximumLineCount(settings['Main'].getint('previewLines'))
            self.text.setFont(font.text)

            self.tag = NElideLabel(self, objectName='DiaryListItemTag')

            # use QToolButton to display icons
            self.datetimeIco = QToolButton(self, objectName='DiaryListItemDtIco')
            minSz = max(font.datetime_m.ascent(), 12*scaleRatio)
            self.datetimeIco.setIconSize(QSize(minSz, minSz))
            self.datetimeIco.setIcon(QIcon(':/calendar.png'))

            self.tagIco = QToolButton(self, objectName='DiaryListItemTagIco')
            minSz = max(font.default_m.ascent(), 12*scaleRatio)
            self.tagIco.setIconSize(QSize(minSz, minSz))
            self.tagIco.setIcon(QIcon(':/tag.png'))

            self._vLayout0 = QVBoxLayout(self)
            self._hLayout0 = QHBoxLayout()
            self._hLayout1 = QHBoxLayout()
            for i in [self._vLayout0, self._hLayout0, self._hLayout1]:
                i.setContentsMargins(0, 0, 0, 0)
                i.setSpacing(0)

            for i in [self.datetimeIco, self.datetime, self.title]:
                self._hLayout0.addWidget(i)
            self._hLayout0.insertSpacing(2, 10)
            for i in [self.tagIco, self.tag]:
                self._hLayout1.addWidget(i)
            self._vLayout0.addLayout(self._hLayout0)
            self._vLayout0.addWidget(self.text)
            self._vLayout0.addLayout(self._hLayout1)

        def refreshStyle(self):
            """Must be called after dynamic property changed"""
            refreshStyle(self)
            # no need to call self.update here

        def setTexts(self, dt, text, title, tags):
            # Some layout behaviours are full of mystery, even changing order of
            # calls will break the UI
            self.datetime.setText(datetimeTrans(dt))
            # without this width of dt will not be updated (for performance reason?)
            self._hLayout0.activate()
            # width of title area depends on itemW's width
            self.title.setText(
                font.title_m.elidedText(title, Qt.ElideRight, self.title.width()))
            self.text.setText(text)
            if tags:
                tags = ' \u2022 '.join(tags.split())  # use bullet to separate
                self.tag.setText(tags)
            self.tag.setVisible(bool(tags))
            self.tagIco.setVisible(bool(tags))

        def refreshHeightInfo(self):
            self.heightWithTag = self.sizeHint().height()
            self.heightNoTag = self.heightWithTag - self._hLayout1.sizeHint().height()

    def __init__(self):
        super().__init__()
        self._itemW = self.ItemWidget()
        self._itemW.refreshHeightInfo()

    def paint(self, painter, option, index):
        row = index.row()

        self._itemW.resize(option.rect.size())
        self._itemW.setTexts(*(index.sibling(row, i).data() for i in range(1, 5)))
        self._itemW.setProperty('selected', bool(option.state & QStyle.State_Selected))
        self._itemW.setProperty('active', bool(option.state & QStyle.State_Active))
        self._itemW.refreshStyle()

        # don't use offset argument of QWidget.render
        painter.translate(option.rect.topLeft())
        self._itemW.render(painter, QPoint())
        painter.resetTransform()

    def sizeHint(self, option, index):
        hasTag = bool(index.sibling(index.row(), 4).data())
        return QSize(-1, self._itemW.heightWithTag if hasTag else self._itemW.heightNoTag)


class DiaryListScrollBar(QScrollBar):
    """Annotated scrollbar."""
    wantSetRow = Signal(int)

    def __init__(self, parent):
        super().__init__(parent, objectName='diaryListSB')
        self._poses = ()
        self._pairs = ()  # year: row
        self._color = QColor('gold')

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._poses:
            return
        p = QPainter(self)
        # avoid painting on slider handle
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove = self.style().subControlRect(QStyle.CC_ScrollBar, opt,
                                             QStyle.SC_ScrollBarGroove, self)
        slider = self.style().subControlRect(QStyle.CC_ScrollBar, opt,
                                             QStyle.SC_ScrollBarSlider, self)
        p.setClipRegion(QRegion(groove) - QRegion(slider), Qt.IntersectClip)

        x, y, w, h = groove.getRect()
        x += 1
        w -= 2
        c = self._color
        c.setAlpha(70)
        p.setBrush(c)
        c.setAlpha(145)
        p.setPen(QPen(c, scaleRatio))
        p.drawRects([QRect(x, y+h*i, w, 3*scaleRatio) for i in self._poses])

    def contextMenuEvent(self, event):
        """Used to jump to the first day of years. Original menu is almost useless."""
        menu = QMenu()
        menu.addAction(QAction(self.tr('Go to the first diary of each year'), menu, enabled=False))
        for year, row in self._pairs:
            menu.addAction(QAction(str(year), menu,
                                   triggered=lambda r=row: self.wantSetRow.emit(r)))
        menu.exec_(event.globalPos())
        menu.deleteLater()

    def setPositions(self, rowCount, pairs):
        self._poses = tuple(p / rowCount for _, p in pairs)
        self._pairs = pairs

    annotateColor = NProperty(QColor, '_color')


class DiaryList(QListView):
    """Main List that display preview of diaries"""
    startLoading = Signal()
    countChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._delegate = None
        # ScrollPerPixel means user can draw scroll bar and move list items pixel by pixel,
        # but mouse wheel still scroll item by item (the number of items scrolled depends on
        # qApp.wheelScrollLines)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.scrollbar = DiaryListScrollBar(self)
        self.scrollbar.wantSetRow.connect(self.setRow)
        self.setVerticalScrollBar(self.scrollbar)

        self.setupTheme()
        # disable default editor. Editor is implemented in the View
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.originModel = DiaryModel(self)
        self.modelProxy = MultiSortFilterProxyModel(self)
        self.modelProxy.setSourceModel(self.originModel)
        self.modelProxy.setDynamicSortFilter(True)
        self.modelProxy.addFilter([db.TAGS], cs=Qt.CaseSensitive)
        self.modelProxy.addFilter([db.TITLE, db.TEXT], cs=Qt.CaseInsensitive)
        self.modelProxy.addFilter([db.DATETIME])
        self.setModel(self.modelProxy)
        self.sort()

        self.editAct = QAction(self.tr('Edit'), self)
        self.delAct = QAction(makeQIcon(':/menu/list-delete.png', scaled2x=True),
                              self.tr('Delete'), self, shortcut=QKeySequence.Delete)
        self.randAct = QAction(makeQIcon(':/menu/random-big.png', scaled2x=True),
                               self.tr('Random'), self,
                               shortcut=QKeySequence(Qt.Key_F7), triggered=self.selectRandomly)
        self.gotoAct = QAction(self.tr('Go to location'), self)
        for i in (self.editAct, self.delAct, self.randAct, self.gotoAct):
            self.addAction(i)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction(self.editAct)
        menu.addAction(self.delAct)
        menu.addSeparator()
        menu.addAction(self.randAct)
        selCount = len(self.selectedIndexes())
        if selCount == 1 and self.modelProxy.isFiltered():
            menu.addAction(self.gotoAct)
        self.editAct.setDisabled(selCount != 1)
        self.delAct.setDisabled(selCount == 0)
        self.randAct.setDisabled(self.modelProxy.rowCount() == 0)
        menu.exec_(event.globalPos())

    def selectAll(self):
        """Prevent original implement to select invisible columns from the Table Model."""
        sel = QItemSelection(self.model().index(0, 0),
                             self.model().index(self.model().rowCount()-1, 0))
        self.selectionModel().select(sel, QItemSelectionModel.ClearAndSelect)

    def setRow(self, row):
        self.setCurrentIndex(self.modelProxy.index(row, 0))

    def selectRandomly(self):
        self.setRow(random.randrange(0, self.modelProxy.rowCount()))

    def load(self):
        self.startLoading.emit()
        self.originModel.loadFromDb()
        self.setAnnotatedScrollbar()
        self.countChanged.emit()

    def setupTheme(self):
        theme = settings['Main']['theme']
        self._delegate = {'colorful': DiaryListDelegateColorful}.get(theme, DiaryListDelegate)()
        self.setItemDelegate(self._delegate)
        if self.isVisible():
            # force items to be laid again
            self.setSpacing(self.spacing())
            self.setAnnotatedScrollbar()

    def reload(self):
        self.originModel.clear()
        self.load()

    def handleExport(self, path, export_all):
        if export_all:
            selected = None
        else:
            selected = list(map(self.getDiaryDict, self.selectedIndexes()))
        db.export_txt(path, selected)

    def getDiaryDict(self, idx):
        """Get a diary dict by its index in proxy model. Diary dict is only used by Editor."""
        return self.originModel.getDiaryDictByRow(self.modelProxy.mapToSource(idx).row())

    def sort(self):
        sortBy = settings['Main']['listSortBy']
        sortByCol = getattr(DiaryModel, sortBy.upper(), DiaryModel.DATETIME)
        reverse = settings['Main'].getboolean('listReverse')
        self.modelProxy.sort(sortByCol,
                             Qt.DescendingOrder if reverse else Qt.AscendingOrder)
        if self.isVisible():
            self.setAnnotatedScrollbar()

    def setAnnotatedScrollbar(self, show=None):
        if show is not False and settings['Main'].getboolean('listAnnotated'):
            self.scrollbar.setPositions(self.originModel.rowCount(), self.originModel.getYearFirsts())
            self.scrollbar.update()
        else:
            self.scrollbar.poses = ()

    def _setFilter(self, filterKey, s):
        self.modelProxy.setFilterPattern(filterKey, s)
        self.setAnnotatedScrollbar(False if s else not self.modelProxy.isFiltered())
        self.countChanged.emit()

    def setFilterBySearchString(self, s):
        self._setFilter(1, s)

    def setFilterByTag(self, s):
        self._setFilter(0, s)

    def setFilterByDatetime(self, s):
        self._setFilter(2, s)

    @Slot(str)
    def refreshFilteredTags(self, newTagName):
        """Update items with old tag after a tag's name changed, and update filter (
        Right click tag item and rename it will always set filter)."""
        model, modelP = self.originModel, self.modelProxy
        needRefresh = [modelP.mapToSource(modelP.index(i, 0))
                       for i in range(modelP.rowCount())]
        for i in needRefresh:
            diary = db[i.data()]  # lazy
            model.setData(i.sibling(i.row(), DiaryModel.TAGS), diary[DiaryModel.TAGS])
        self.setFilterByTag(newTagName)
