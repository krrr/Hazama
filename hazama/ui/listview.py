from PySide.QtGui import *
from PySide.QtCore import *
from ui import font, datetimeTrans, currentDatetime
from ui.editor import Editor
from ui.customobjects import NTextDocument, MultiSortFilterProxyModel
from config import settings, nikki
import logging
import random


class NListDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(NListDelegate, self).__init__(parent)
        self.title_h = max(QFontInfo(font.title).pixelSize(),
                           QFontInfo(font.date).pixelSize()) + 4  # dt and title font area
        self.titleArea_h = self.title_h + 4
        self.text_h = (QFontMetrics(font.text).lineSpacing() *
                       settings['Main'].getint('previewlines', 4))
        self.tagPath_h = QFontInfo(qApp.font()).pixelSize() + 4
        self.tag_h = self.tagPath_h + 4
        self.dt_w = QFontMetrics(font.title).width('2000/00/00 00:00') + 20
        self.all_h = None  # updated in sizeHint before each item being painting
        # doc is used to draw text(diary's body)
        self.doc = NTextDocument()
        self.doc.setDefaultFont(font.text)
        self.doc.setUndoRedoEnabled(False)
        self.doc.setDocumentMargin(0)
        # setup colors
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
        painter.setPen(Qt.black)
        painter.setFont(font.date)
        painter.drawText(x+14, y+self.titleArea_h-self.title_h, w, self.title_h,
                         Qt.AlignVCenter, datetimeTrans(dt))
        if title:
            painter.setFont(font.title)
            title_w = w-self.dt_w-13
            title = font.title_m.elidedText(title, Qt.ElideRight, title_w)
            painter.drawText(x+self.dt_w, y+self.titleArea_h-self.title_h, title_w, self.title_h,
                             Qt.AlignVCenter | Qt.AlignRight, title)
        # draw text
        painter.save()
        self.doc.setText(text, formats)
        self.doc.setTextWidth(w-26)
        painter.translate(x+14, y+self.titleArea_h+2)
        self.doc.drawContents(painter, QRect(0, 0, w-26, self.text_h))
        painter.restore()
        # draw tags
        if tags:
            painter.save()
            painter.setPen(self.c_gray)
            painter.setFont(font.default)
            painter.translate(x + 15, y+self.titleArea_h+6+self.text_h)
            for t in tags.split():
                w = font.default_m.width(t) + 4
                tagPath = QPainterPath()
                tagPath.moveTo(8, 0)
                tagPath.lineTo(8+w, 0)
                tagPath.lineTo(8+w, self.tagPath_h)
                tagPath.lineTo(8, self.tagPath_h)
                tagPath.lineTo(0, self.tagPath_h/2)
                tagPath.closeSubpath()
                painter.drawPath(tagPath)
                painter.drawText(8, 1, w, self.tagPath_h, Qt.AlignCenter, t)
                painter.translate(w+15, 0)  # translate by offset
            painter.restore()

    def sizeHint(self, option, index):
        tag_h = self.tag_h if index.sibling(index.row(), 4).data() else 0
        self.all_h = self.titleArea_h + 2 + self.text_h + tag_h + 6
        return QSize(-1, self.all_h+3)  # 3 is spacing between entries

    def createEditor(self, *__):
        """Disable default editor. Editor is implemented in the View"""
        return None


class TListDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(TListDelegate, self).__init__(parent)
        self.h = QFontInfo(font.default).pixelSize()+8

    def paint(self, painter, option, index):
        x, y, w = option.rect.x(), option.rect.y(), option.rect.width()
        tag, count = index.data(Qt.DisplayRole), str(index.data(Qt.UserRole))
        painter.setFont(font.default)
        selected = bool(option.state & QStyle.State_Selected)
        textArea = QRect(x+4, y, w-8, self.h)
        if index.row() == 0:  # row 0 is always All(clear tag filter)
            painter.setPen(QColor(80, 80, 80))
            painter.drawText(textArea,
                             Qt.AlignVCenter | Qt.AlignLeft,
                             tag)
        else:
            painter.setPen(QColor(209, 109, 63))
            painter.drawLine(x, y, w, y)
            if selected:
                painter.setPen(QColor(181, 61, 0))
                painter.setBrush(QColor(250, 250, 250))
                painter.drawRect(x, y+1, w-1, self.h-2)
            # draw tag
            painter.setPen(QColor(20, 20, 20) if selected else
                           QColor(80, 80, 80))
            tag = font.default_m.elidedText(tag, Qt.ElideRight,
                                            w-font.date_m.width(count)-12)
            painter.drawText(textArea, Qt.AlignVCenter | Qt.AlignLeft, tag)
            # draw tag count
            painter.setFont(font.date)
            painter.drawText(textArea, Qt.AlignVCenter | Qt.AlignRight, count)

    def sizeHint(self, option, index):
        return QSize(-1, self.h)


class TagList(QListWidget):
    currentTagChanged = Signal(str)  # str is tag-name or ''

    def __init__(self, *args, **kwargs):
        super(TagList, self).__init__(*args, **kwargs)
        self.setItemDelegate(TListDelegate(self))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setUniformItemSizes(True)
        self.trackList = None  # update in mousePressEvent
        self.currentItemChanged.connect(self.emitCurrentTagChanged)

    def load(self):
        logging.debug('Tag List load')
        item_all = QListWidgetItem(self)
        item_all.setData(Qt.DisplayRole, self.tr('All'))
        for t in nikki.gettag(getcount=True):
            item = QListWidgetItem(self)
            item.setData(Qt.DisplayRole, t[0])
            item.setData(Qt.UserRole, t[1])

    def reload(self):
        if self.isVisible():
            try:
                currentTag = self.currentItem().data(Qt.DisplayRole)
            except AttributeError:  # no selection
                currentTag = None
            self.clear()
            self.load()
            if currentTag:
                try:
                    item = self.findItems(currentTag, Qt.MatchFixedString)[0]
                except IndexError:
                    item = self.item(0)
                self.setCurrentItem(item)

    def emitCurrentTagChanged(self, currentItem):
        try:
            text = currentItem.data(Qt.DisplayRole)
        except AttributeError:  # no selection
            return
        self.currentTagChanged.emit('' if text == self.tr('All') else text)

    # all three events below for drag scroll
    def mousePressEvent(self, event):
        self.trackList = []

    def mouseMoveEvent(self, event):
        if self.trackList is not None:
            self.trackList.append(event.pos().y())
            if len(self.trackList) > 4:
                change = self.trackList[-1] - self.trackList[-2]
                scrollbar = self.verticalScrollBar()
                scrollbar.setValue(scrollbar.value() - change)

    def mouseReleaseEvent(self, event):
        if self.trackList is not None:
            if len(self.trackList) <= 4:  # haven't moved
                pEvent = QMouseEvent(QEvent.MouseButtonPress, event.pos(),
                                     event.globalPos(), Qt.LeftButton,
                                     Qt.LeftButton, Qt.NoModifier)
                QListWidget.mousePressEvent(self, pEvent)
        self.trackList = None


class NikkiList(QListView):
    countChanged = Signal()
    tagsChanged = Signal()

    def __init__(self, parent=None):
        super(NikkiList, self).__init__(parent)
        self.setSelectionMode(self.ExtendedSelection)
        self.setItemDelegate(NListDelegate(self))
        self.setSpacing(0)
        # setup models
        self.model = QStandardItemModel(0, 7, self)
        self.fillModel(self.model)
        self.modelProxy = MultiSortFilterProxyModel(self)
        self.modelProxy.setSourceModel(self.model)
        self.modelProxy.setDynamicSortFilter(True)
        self.modelProxy.addFilterKey(0, cols=[4])
        self.modelProxy.addFilterKey(1, cols=[1, 2, 3])
        self.setModel(self.modelProxy)
        self.sort()
        # setup context menu
        self.editAct = QAction(self.tr('Edit'), self,
                               triggered=self.startEditor)
        self.delAct = QAction(QIcon(':/menu/list_delete.png'),
                              self.tr('Delete'), self,
                              shortcut=QKeySequence.Delete,
                              triggered=self.delNikki)
        self.randAct = QAction(QIcon(':/menu/random.png'),
                               self.tr('Random'), self,
                               shortcut=QKeySequence(Qt.Key_F7),
                               triggered=self.selectRandomly)
        for i in [self.editAct, self.delAct, self.randAct]: self.addAction(i)
        self.menu = QMenu(self)
        self.menu.addAction(self.editAct)
        self.menu.addAction(self.delAct)
        self.menu.addSeparator()
        self.menu.addAction(self.randAct)
        # setup editors
        self.editors = {}
        self.doubleClicked.connect(self.startEditor)
        self.activated.connect(self.startEditor)

    def contextMenuEvent(self, event):
        selectionCount = len(self.selectedIndexes())
        self.editAct.setDisabled(selectionCount != 1)
        self.delAct.setDisabled(selectionCount == 0)
        self.randAct.setDisabled(selectionCount == 0)
        self.menu.popup(event.globalPos())

    def selectRandomly(self):
        randRow = random.randrange(0, self.modelProxy.rowCount())
        self.setCurrentIndex(self.modelProxy.index(randRow, 0))

    def startEditor(self, index=None):
        if index is None:  # called by context-menu
            index = self.currentIndex()
        row = index.row()
        id, dt, text, title, tags, formats = (index.sibling(row, i).data()
                                              for i in range(6))
        if id in self.editors:
            self.editors[id].activateWindow()
        else:
            editor = Editor()
            editor.datetime = dt
            editor.id = id
            editor.tagEditor.setText(tags)
            editor.titleEditor.setText(title)
            editor.textEditor.setText(text, formats)
            self.editors[id] = editor
            editor.closed.connect(self.closeEditor)
            editor.preSc.activated.connect(self.editorPrevious)
            editor.nextSc.activated.connect(self.editorNext)
            editor.show()
            return id

    def startEditorNew(self):
        if -1 in self.editors:
            self.editors[-1].activateWindow()
        else:
            editor = Editor()
            editor.id = -1
            self.editors[-1] = editor
            editor.closed.connect(self.closeEditor)
            editor.show()

    def closeEditor(self, id, needSave):
        """Write editor's data to model and database, and destroy editor"""
        editor = self.editors[id]
        isNew = id == -1
        if needSave:
            dt = currentDatetime() if editor.datetime is None else editor.datetime
            text = editor.textEditor.toPlainText()
            title = editor.titleEditor.text()
            tags = editor.tagEditor.text()
            formats = editor.textEditor.getFormats()
            realId = nikki.save(id=id, datetime=dt, formats=formats,
                                text=text, title=title, new=isNew,
                                tags=tags if editor.tagModified else None)
            # write to model
            self.modelProxy.setSourceModel(None)
            if isNew:
                self.model.insertRow(0)
                row = 0
            else:
                row = self.model.findItems(str(realId))[0].row()
            cols = (realId, dt, text, title, tags, formats, len(text))
            for c, d in zip(range(7), cols):
                self.model.setData(self.model.index(row, c), d)
            self.modelProxy.setSourceModel(self.model)
            self.setCurrentIndex(self.modelProxy.mapFromSource(
                self.model.index(row, 0)))
        if isNew:
            self.countChanged.emit()
        if editor.tagModified:
            self.tagsChanged.emit()
        editor.deleteLater()
        del self.editors[id]

    @staticmethod
    def fillModel(model):
        for i in nikki:
            model.insertRow(0)
            model.setData(model.index(0, 0), i['id'])
            model.setData(model.index(0, 1), i['datetime'])
            model.setData(model.index(0, 2), i['text'])
            model.setData(model.index(0, 3), i['title'])
            model.setData(model.index(0, 4), i['tags'])
            model.setData(model.index(0, 5), i['formats'])
            model.setData(model.index(0, 6), len(i['text']))

    def reload(self):
        self.modelProxy.setSourceModel(None)
        self.model.deleteLater()
        self.model = QStandardItemModel(0, 7, self)
        self.fillModel(self.model)
        self.modelProxy.setSourceModel(self.model)

    def delNikki(self):
        if len(self.selectedIndexes()) == 0: return
        ret = QMessageBox.question(self, self.tr('Delete selected diaries'),
                                   self.tr('Selected diaries will be deleted '
                                           'permanently!'),
                                   QMessageBox.Yes | QMessageBox.No)

        if ret == QMessageBox.Yes:
            indexes = [self.modelProxy.mapToSource(i)
                       for i in self.selectedIndexes()]
            for i in indexes: nikki.delete(i.data())
            for i in sorted([i.row() for i in indexes], reverse=True):
                self.model.removeRow(i)
            self.countChanged.emit()
            self.tagsChanged.emit()  # tags might changed

    def handleExport(self, export_all):
        path, _type = QFileDialog.getSaveFileName(
            parent=self,
            caption=self.tr('Export Diary'),
            filter=self.tr('Plain Text (*.txt);;Rich Text (*.rtf)'))
        if path == '': return    # dialog canceled
        if _type.endswith('txt)'):
            selected = (None if export_all else
                        [i.data(2) for i in self.selectedItems()])
            nikki.exporttxt(path, selected)

    def resetDelegate(self):
        self.setItemDelegate(NListDelegate(self))
        # without this spacing between items will be strange
        self.setSpacing(0)

    def sort(self):
        sortBy = settings['Main'].get('listsortby', 'datetime')
        sortByCol = {'datetime': 1, 'title': 3, 'length': 6}.get(sortBy, 1)
        reverse = settings['Main'].getint('listreverse', 1)
        self.modelProxy.sort(sortByCol,
                             Qt.DescendingOrder if reverse else Qt.AscendingOrder)

    def editorNext(self):
        self.editorMove(1)

    def editorPrevious(self):
        self.editorMove(-1)

    def editorMove(self, step):
        if len(self.editors) > 1: return
        id = list(self.editors.keys())[0]
        assert id != -1
        index = self.model.findItems(str(id))[0].index()
        rowInProxy = self.modelProxy.mapFromSource(index).row()
        if ((step == -1 and rowInProxy == 0) or
           (step == 1 and rowInProxy == self.modelProxy.rowCount() - 1)):
             return
        self.clearSelection()
        self.setCurrentIndex(self.modelProxy.index(rowInProxy+step, 0))
        geo = self.editors[id].saveGeometry()
        newId = self.startEditor()
        # start new before close old to avoid focus changing, but we should
        # set geometry twice
        self.editors[id].closeNoSave()
        self.editors[newId].restoreGeometry(geo)

    def setFilterBySearchString(self, s):
        self.modelProxy.setFilterFixedString(1, s)

    def setFilterByTag(self, s):
        self.modelProxy.setFilterFixedString(0, s)

