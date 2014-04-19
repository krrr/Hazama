from PySide.QtGui import *
from PySide.QtCore import *
from . import font, dt_trans
from .editor import Editor
from .customobjects import NTextDocument
from config import settings, nikki
import logging
import random


class NListDelegate(QStyledItemDelegate):
    stylesheet = ('QListWidget{background-color: rgb(242, 241, 231);'
                  'border: solid 0px; margin-top: 1px}')

    def __init__(self, parent=None):
        super(NListDelegate, self).__init__(parent)
        self.title_h = QFontInfo(font.title).pixelSize() + 10  # title area height
        self.text_h = (QFontMetrics(font.text).lineSpacing() *
                       settings['Main'].getint('previewlines', 4))
        self.tagpath_h = QFontInfo(qApp.font()).pixelSize() + 4
        self.tag_h = self.tagpath_h + 4
        self.dt_w = QFontMetrics(font.title).width('2000/00/00 00:00') + 20
        # doc is used to draw text(diary's body)
        self.doc = NTextDocument()
        self.doc.setDefaultFont(font.text)
        self.doc.setUndoRedoEnabled(False)
        self.doc.setDocumentMargin(0)
        # setup colors
        self.c_bg = QColor(255, 236, 176)
        self.c_border = QColor(214, 172, 41)
        self.c_unselbg = QColor(255, 236, 176, 40)
        self.c_gray = QColor(93, 73, 57)

    def paint(self, painter, option, index):
        x, y, w = option.rect.x(), option.rect.y(), option.rect.width()-1
        row = index.data()
        selected = bool(option.state & QStyle.State_Selected)
        active = bool(option.state & QStyle.State_Active)
        # draw border and background
        painter.setPen(self.c_border)
        painter.setBrush(self.c_bg if selected and active else
                         self.c_unselbg)
        border = QRect(x+1, y, w-2, self.all_h)
        painter.drawRect(border)
        if selected:
            innerborder = QRect(x+2, y+1, w-4, self.all_h-2)
            pen = QPen()
            pen.setStyle(Qt.DashLine)
            pen.setColor(self.c_gray)
            painter.setPen(pen)
            painter.drawRect(innerborder)
        # draw datetime and title
        painter.setPen(self.c_gray)
        painter.drawLine(x+10, y+self.title_h, x+w-10, y+self.title_h)
        painter.setPen(Qt.black)
        painter.setFont(font.date)
        painter.drawText(x+14, y, w, self.title_h, Qt.AlignBottom,
                         dt_trans(row['datetime']))
        if row['title']:
            painter.setFont(font.title)
            title_w = w-self.dt_w-13
            title = font.title_m.elidedText(row['title'], Qt.ElideRight, title_w)
            painter.drawText(x+self.dt_w, y, title_w, self.title_h,
                             Qt.AlignBottom | Qt.AlignRight, title)
        # draw text
        painter.save()
        formats = None if row['plaintext'] else nikki.getformat(row['id'])
        self.doc.setText(row['text'], formats)
        self.doc.setTextWidth(w-26)
        painter.translate(x+14, y+self.title_h+2)
        self.doc.drawContents(painter, QRect(0, 0, w-26, self.text_h))
        painter.restore()
        # draw tags
        if row['tags']:
            painter.save()
            painter.setPen(self.c_gray)
            painter.setFont(qApp.font())
            painter.translate(x + 15, y+self.title_h+6+self.text_h)
            for t in row['tags'].split():
                w = font.default_m.width(t) + 4
                tagpath = QPainterPath()
                tagpath.moveTo(8, 0)
                tagpath.lineTo(8+w, 0)
                tagpath.lineTo(8+w, self.tagpath_h)
                tagpath.lineTo(8, self.tagpath_h)
                tagpath.lineTo(0, self.tagpath_h/2)
                tagpath.closeSubpath()
                painter.drawPath(tagpath)
                painter.drawText(8, 1, w, self.tagpath_h, Qt.AlignCenter, t)
                painter.translate(w+15, 0)  # translate by offset
            painter.restore()

    def sizeHint(self, option, index):
        tag_h = self.tag_h if index.data()['tags'] else 0
        self.all_h = self.title_h + self.text_h + tag_h + 10
        return QSize(-1, self.all_h+3)  # 3 is spacing between entries


class TListDelegate(QStyledItemDelegate):
    """Default TagList Delegate.Also contains TList's stylesheet"""
    stylesheet = ('QListWidget{background-color: rgb(234,182,138);'
                  'border: solid 0px}')

    def __init__(self, parent=None):
        super(TListDelegate, self).__init__(parent)
        self.h = QFontInfo(font.default).pixelSize()+8

    def paint(self, painter, option, index):
        x, y, w = option.rect.x(), option.rect.y(), option.rect.width()
        tag, count = index.data(3), str(index.data(2))
        painter.setFont(font.default)
        selected = bool(option.state & QStyle.State_Selected)
        textarea = QRect(x+4, y, w-8, self.h)
        if index.row() == 0:  # row 0 is always All(clear tag filter)
            painter.setPen(QColor(80, 80, 80))
            painter.drawText(textarea,
                             Qt.AlignVCenter | Qt.AlignLeft,
                             qApp.translate('TagList', 'All'))
        else:
            painter.setPen(QColor(209, 109, 63))
            painter.drawLine(x, y, w, y)
            if selected:
                trect = QRect(x, y+1, w-1, self.h-2)
                painter.setPen(QColor(181, 61, 0))
                painter.setBrush(QColor(250, 250, 250))
                painter.drawRect(trect)
            # draw tag
            painter.setPen(QColor(20, 20, 20) if selected else
                           QColor(80, 80, 80))
            tag = font.default_m.elidedText(tag, Qt.ElideRight,
                                            w-font.date_m.width(count)-12)
            painter.drawText(textarea, Qt.AlignVCenter|Qt.AlignLeft, tag)
            # draw tag count
            painter.setFont(font.date)
            painter.drawText(textarea, Qt.AlignVCenter|Qt.AlignRight, count)

    def sizeHint(self, option, index):
        return QSize(-1, self.h)


class TagList(QListWidget):
    def __init__(self, *args, **kwargs):
        super(TagList, self).__init__(*args, **kwargs)
        self.setItemDelegate(TListDelegate(self))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setUniformItemSizes(True)
        self.setStyleSheet(TListDelegate.stylesheet)

    def load(self):
        logging.info('Tag List load')
        self.clear()  # this may emit unexpected signal when has selection
        item_all = QListWidgetItem(self)
        item_all.setData(1, 'All')
        for t in nikki.gettag(getcount=True):
            item = QListWidgetItem(self)
            item.setData(3, t[1])
            item.setData(2, t[2])
            item.setData(1, t[0])

    # all three events below for drag scroll
    def mousePressEvent(self, event):
        self.tracklst = []

    def mouseMoveEvent(self, event):
        if self.tracklst is not None:
            self.tracklst.append(event.pos().y())
            if len(self.tracklst) > 4:
                change = self.tracklst[-1] - self.tracklst[-2]
                scrollbar = self.verticalScrollBar()
                scrollbar.setValue(scrollbar.value() - change)

    def mouseReleaseEvent(self, event):
        if self.tracklst is not None:
            if len(self.tracklst) <= 4:  # haven't moved
                pevent = QMouseEvent(QEvent.MouseButtonPress, event.pos(),
                                     event.globalPos(), Qt.LeftButton,
                                     Qt.LeftButton, Qt.NoModifier)
                QListWidget.mousePressEvent(self, pevent)

        self.tracklst = None


class NikkiList(QListWidget):
    reloaded = Signal()
    needRefresh = Signal(bool, bool)  # (countlabel, taglist)

    def __init__(self, *args, **kwargs):
        super(NikkiList, self).__init__(*args, **kwargs)
        self.setMinimumSize(350, 200)
        self.editors = {}

        self.setSelectionMode(self.ExtendedSelection)
        self.itemDoubleClicked.connect(self.startEditor)

        self.setItemDelegate(NListDelegate(self))
        self.setStyleSheet(NListDelegate.stylesheet)

        # setup context menu
        self.editAct = QAction(self.tr('Edit'), self,
                               shortcut=QKeySequence(Qt.Key_Return),
                               triggered=self.startEditor)
        self.delAct = QAction(self.tr('Delete'), self,
                              shortcut=QKeySequence.Delete,
                              triggered=self.delNikki)
        self.selAct = QAction(self.tr('Random'), self,
                              shortcut=QKeySequence(Qt.Key_F7),
                              triggered=self.selectRandomly)
        for i in [self.editAct, self.delAct, self.selAct]: self.addAction(i)
        self.menu = QMenu(self)
        self.menu.addAction(self.editAct)
        self.menu.addAction(self.delAct)
        self.menu.addSeparator()
        self.menu.addAction(self.selAct)

    def contextMenuEvent(self, event):
        selection_count = len(self.selectedItems())
        self.editAct.setDisabled(selection_count != 1)
        self.delAct.setDisabled(selection_count == 0)
        self.selAct.setDisabled(selection_count == 0)
        self.menu.popup(event.globalPos())

    def startEditor(self, item=None, new=False):
        if new:  # called by newNikki method
            curtitem = row = None
            id = -1
        else:  # called by doubleclick event or contextmenu or key-shortcut
            curtitem = item if item else self.selectedItems()[0]
            row = curtitem.data(2)
            id = row['id']
        if id in self.editors:
            self.editors[id].activateWindow()
        else:  # create new editor
            editor = Editor(editorid=id, new=new, row=row)
            editor.closed.connect(self.on_editor_closed)
            self.editors[id] = editor
            editor.item = curtitem
            if not new:
                editor.nextSc.activated.connect(self.editorNext)
                editor.preSc.activated.connect(self.editorPrevious)
            editor.show()

    def on_editor_closed(self, editorid, nikkiid, tagsModified):
        if nikkiid != -1:
            self.reload(nikkiid)
            self.needRefresh.emit(editorid == -1, tagsModified)
        self.editors[editorid].destroy()
        del self.editors[editorid]

    def delNikki(self):
        ret = QMessageBox.question(self, self.tr('Delete selected diaries'),
                                   self.tr('Selected diaries will be deleted '
                                           'permanently.Do it?'),
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.No: return
        for i in self.selectedItems():
            nikki.delete(i.data(2)['id'])
            self.takeItem(self.row(i))
        self.needRefresh.emit(True, True)

    def newNikki(self):
        self.startEditor(None, True)

    def load(self, *, tagid=None, search=None):
        order, reverse = self.getOrder()
        for row in nikki.sorted(order, reverse, tagid=tagid, search=search):
            item = QListWidgetItem(self)
            item.setData(2, row)
        self.setCurrentRow(0)

    def reload(self, id=None):
        order, reverse = self.getOrder()
        logging.debug('Nikki List reload')
        self.clear()
        if id is None:
            for row in nikki.sorted(order, reverse):
                item = QListWidgetItem(self)
                item.setData(2, row)
        else:
            for row in nikki.sorted(order, reverse):
                if row['id'] == id:
                    rownum = self.count()
                item = QListWidgetItem(self)
                item.setData(2, row)
            self.setCurrentRow(rownum)
        self.reloaded.emit()

    def handleExport(self, export_all):
        path, _type = QFileDialog.getSaveFileName(parent=self,
            caption=self.tr('Export Diary'),
            filter=self.tr('Plain Text (*.txt);;Rich Text (*.rtf)'))
        if path == '': return    # dialog canceled
        if _type.endswith('txt)'):
            selected = (None if export_all else
                        [i.data(2) for i in self.selectedItems()])
            nikki.exporttxt(path, selected)

    @staticmethod
    def getOrder():
        """get sort order(str) and reverse(int) from settings file"""
        order = settings['Main'].get('listorder', 'datetime')
        reverse = settings['Main'].getint('listreverse', 1)
        return order, reverse

    def selectRandomly(self):
        self.setCurrentRow(random.randrange(0, self.count()))

    def editorNext(self):
        self.editorMove(1)

    def editorPrevious(self):
        self.editorMove(-1)

    def editorMove(self, step):
        """Move to the Previous/Next Diary in Editor.Current
        Editor will close without saving,"""
        curtEditor = list(self.editors.values())[0]
        try:
            index = self.row(curtEditor.item)
        except RuntimeError:  # C++ object already deleted
            return
        # disabled when multi-editor or editing new diary(if new,
        # shortcut would not be set) or no item to move on.
        if (len(self.editors) != 1 or index is None or
           (step == 1 and index >= self.count() - 1) or
           (step == -1 and 0 >= index)):
            return
        else:
            self.setCurrentRow(index + step)
            self.startEditor()
            curtEditor.closeNoSave()

    def sortDT(self, checked):
        if checked:
            settings['Main']['listorder'] = 'datetime'
            self.clear()
            self.load()

    def sortTT(self, checked):
        if checked:
            settings['Main']['listorder'] = 'title'
            self.clear()
            self.load()

    def sortLT(self, checked):
        if checked:
            settings['Main']['listorder'] = 'length'
            self.clear()
            self.load()

    def sortRE(self, checked):
        settings['Main']['listreverse'] = str(checked.real)
        self.clear()
        self.load()

