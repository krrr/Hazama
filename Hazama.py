from PySide.QtGui import *
from PySide.QtCore import *
import res
from ui.configdialog import Ui_Settings
from ui.editor import Ui_Editor
from ui.customwidgets import *
from ui.customobjects import *
from db import Nikki

import sys, os
import time
import random
import logging
import locale

__version__ = 0.08


def restart_main():
    "Restart Main Window after language changed in settings."
    logging.debug('restart_main called')
    global main
    geo = main.saveGeometry()
    # delete the only reference to old one
    main = Main()
    main.restoreGeometry(geo)
    main.show()

def set_trans(settings):
    "Install translations"
    lang = settings.value('Main/lang')
    if lang is None:
        settings.setValue('Main/lang', 'en')
    else:
        global trans, transQt
        trans = QTranslator()
        trans.load('lang/'+lang)
        transQt = QTranslator()
        transQt.load('qt_'+lang, QLibraryInfo.location(QLibraryInfo.TranslationsPath))
        for i in [trans, transQt]: qApp.installTranslator(i)
        windowslangstr = {'zh_CN': 'chinese-simplified', 'en': 'english',
                          'ja_JP': 'japanese'}
        locale.setlocale(locale.LC_ALL, windowslangstr[lang])

def backupcheck(dbpath):
    "Check backups and do if necessary.Delete old backups."
    bkpath = 'backup'
    if not os.path.isdir(bkpath): os.mkdir(bkpath)
    dblst = sorted(os.listdir(bkpath))
    fil = lambda x: len(x)>10 and x[4]==x[7]=='-' and x[10]=='_'
    dblst = list(filter(fil, dblst))

    fmt = '%Y-%m-%d'
    today = time.strftime(fmt)
    try:
        newest = dblst[-1]
    except IndexError:  # empty directory
        newest = ''
    if newest.split('_')[0] != today:  # new day
        # make new backup
        import shutil
        shutil.copyfile(dbpath, os.path.join(bkpath,
                                             today+'_%d.db' % nikki.count()))
        logging.info('Everyday backup succeed')
        # delete old backups
        weekbefore = time.strftime(fmt , time.localtime(int(time.time())-604800))
        for dname in dblst:
            if dname < weekbefore:
                os.remove(os.path.join(bkpath, dname))
            else:
                break

def currentdt_str():
    return time.strftime('%Y-%m-%d %H:%M')

def dt_trans_gen():
    dtfmt = settings.value('Main/datetimefmt')
    dfmt = settings.value('Main/datefmt')
    if dtfmt and dfmt:
        def dt_trans(s, dateonly=False):
            try:
                dt = time.strptime(s, '%Y-%m-%d %H:%M')
                return time.strftime(dfmt if dateonly else dtfmt, dt)
            except Exception:
                logging.warning('Failed to translate datetime string')
                return s
    else:
        def dt_trans(s, dateonly=False):
            return s.split()[0] if dateonly else s
    return dt_trans


class NListDelegate(QStyledItemDelegate):
    stylesheet = ('QListWidget{background-color: rgb(242, 241, 231);'
                  'border: solid 0px; margin-top: 1px}')
    def __init__(self):
        super(NListDelegate, self).__init__()
        self.title_h = QFontInfo(titlefont).pixelSize() + 10  # title area height
        self.text_h = (QFontMetrics(textfont).lineSpacing() *
                       int(settings.value('Nlist/previewlines', 4)))
        self.tagpath_h = QFontInfo(qApp.font()).pixelSize() + 4
        self.tag_h = self.tagpath_h + 4
        self.dt_w = QFontMetrics(titlefont).width('2000/00/00 00:00') + 20
        # doc is used to draw text(diary's body)
        self.doc = NTextDocument()
        self.doc.setDefaultFont(textfont)
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
        painter.setFont(datefont)
        painter.drawText(x+14, y, w, self.title_h, Qt.AlignBottom,
                         dt_trans(row['datetime']))
        if row['title']:
            painter.setFont(titlefont)
            title_w = w-self.dt_w-13
            title = ttfontm.elidedText(row['title'], Qt.ElideRight, title_w)
            painter.drawText(x+self.dt_w, y, title_w, self.title_h,
                             Qt.AlignBottom|Qt.AlignRight, title)
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
                w = defontm.width(t) + 4
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
    '''Default TagList(TList) Delegate.Also contains TList's stylesheet'''
    stylesheet = ('QListWidget{background-color: rgb(234,182,138);'
               'border: solid 0px}')
    def __init__(self):
        super(TListDelegate, self).__init__()
        self.h = QFontInfo(defont).pixelSize()+8

    def paint(self, painter, option, index):
        x, y, w= option.rect.x(), option.rect.y(), option.rect.width()
        tag, count = index.data(3), str(index.data(2))
        painter.setFont(defont)
        selected = bool(option.state & QStyle.State_Selected)
        textarea = QRect(x+4, y, w-8, self.h)
        if index.row() == 0:  # row 0 is always All(clear tag filter)
            painter.setPen(QColor(80, 80, 80))
            painter.drawText(textarea,
                             Qt.AlignVCenter|Qt.AlignLeft,
                             qApp.translate('TList', 'All'))
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
            tag = defontm.elidedText(tag, Qt.ElideRight, w-dfontm.width(count)-12)
            painter.drawText(textarea, Qt.AlignVCenter|Qt.AlignLeft, tag)
            # draw tag count
            painter.setFont(datefont)
            painter.drawText(textarea, Qt.AlignVCenter|Qt.AlignRight, count)

    def sizeHint(self, option, index):
        return QSize(-1, self.h)


class NList(QListWidget):
    reloaded = Signal()
    needRefresh = Signal(bool, bool)  # (countlabel, taglist)
    def __init__(self):
        super(NList, self).__init__()
        self.setMinimumSize(350,200)
        self.editors = {}

        self.setSelectionMode(self.ExtendedSelection)
        self.itemDoubleClicked.connect(self.starteditor)

        self.setItemDelegate(NListDelegate())
        self.setStyleSheet(NListDelegate.stylesheet)

        # Context Menu
        self.editAct = QAction(self.tr('Edit'), self,
                               shortcut=QKeySequence(Qt.Key_Return),
                               triggered=self.starteditor)
        self.delAct = QAction(self.tr('Delete'), self,
                              shortcut=QKeySequence.Delete,
                              triggered=self.delNikki)
        self.selAct = QAction(self.tr('Random'), self,
                              shortcut=QKeySequence(Qt.Key_F7),
                              triggered=self.selectRandomly)
        for i in [self.editAct, self.delAct, self.selAct]: self.addAction(i)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction(self.editAct)
        menu.addAction(self.delAct)
        menu.addSeparator()
        menu.addAction(self.selAct)

        selcount = len(self.selectedItems())
        self.editAct.setDisabled(True if selcount!=1 else False)
        self.delAct.setDisabled(False if selcount!=0 else True)
        self.selAct.setDisabled(False if selcount!=0 else True)
        menu.popup(event.globalPos())

    def starteditor(self, item=None, new=False):
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
            editor = Editor(new=new, row=row)
            editor.closed.connect(self.on_editor_closed)
            self.editors[id] = editor
            editor.setEditorId(id)
            editor.item = curtitem
            if not new:
                editor.nextSc.activated.connect(self.editorNext)
                editor.preSc.activated.connect(self.editorPrevious)
            editor.show()

    def on_editor_closed(self, editorid, nikkiid, tagsModified):
        if nikkiid != -1:
            self.reload(nikkiid)
            self.needRefresh.emit(editorid==-1, tagsModified)
        del self.editors[editorid]

    def delNikki(self):
        msgbox = QMessageBox(QMessageBox.NoIcon,
                             self.tr('Delete selected diaries'),
                             self.tr('Selected diaries will be deleted '
                                     'permanently.Do it?'),
                             QMessageBox.Yes|QMessageBox.No,
                             parent=self)
        msgbox.setDefaultButton(QMessageBox.Cancel)
        ret = msgbox.exec_()
        if ret == QMessageBox.Yes:
            for i in self.selectedItems():
                nikki.delete(i.data(2)['id'])
                self.takeItem(self.row(i))
            self.needRefresh.emit(True, True)
        # QWidget.destroy() doesn't work
        msgbox.deleteLater()

    def newNikki(self):
        self.starteditor(None, True)

    def load(self, *, tagid=None, search=None):
        order, reverse = self.getOrder()
        for row in nikki.sorted(order, reverse, tagid=tagid, search=search):
            item = QListWidgetItem(self)
            item.setData(2, row)
        self.setCurrentRow(0)

    def reload(self, id):
        order, reverse = self.getOrder()
        logging.debug('Nikki List reload')
        self.clear()
        for row in nikki.sorted(order, reverse):
            if row['id'] == id:
                rownum = self.count()
            item = QListWidgetItem(self)
            item.setData(2, row)
        self.setCurrentRow(rownum)
        self.reloaded.emit()

    def getOrder(self):
        "get sort order(str) and reverse(int) from settings file"
        order = settings.value('NList/sortOrder', 'datetime')
        reverse = int(settings.value('NList/sortReverse', 1))
        return order, reverse

    def selectRandomly(self):
        self.setCurrentRow(random.randrange(0, self.count()))

    def editorNext(self):
        self.editorMove(1)

    def editorPrevious(self):
        self.editorMove(-1)

    def editorMove(self, step):
        '''Move to the Previous/Next Diary in Editor.Current
        Editor will close without saving,'''
        curtEditor = [k for k in self.editors.values()][0]
        try:
            index = self.row(curtEditor.item)
        except RuntimeError:  # C++ object already deleted
            return
        # disabled when multi-editor or editing new diary(if new,
        # shortcut would not be set) or no item to move on.
        if len(self.editors) != 1 or index is None:
            return
        elif step == 1 and not index < self.count()-1:
            return
        elif step == -1 and not 0 < index:
            return
        else:
            self.setCurrentRow(index+step)
            self.starteditor()
            curtEditor.closeNoSave()

    def sortDT(self, checked):
        if checked:
            settings.setValue('NList/sortOrder', 'datetime')
            self.clear()
            self.load()

    def sortTT(self, checked):
        if checked:
            settings.setValue('NList/sortOrder', 'title')
            self.clear()
            self.load()

    def sortLT(self, checked):
        if checked:
            settings.setValue('NList/sortOrder', 'length')
            self.clear()
            self.load()

    def sortRE(self, checked):
        settings.setValue('NList/sortReverse', int(checked))
        self.clear()
        self.load()


class Editor(QWidget, Ui_Editor):
    '''Widget used to edit diary's body,title,tag,datetime.
    Signal closed: (editorid, nikkiid, tagsModified),nikkiid is -1
    if canceled or no need to save.
    '''
    closed = Signal(int, int, bool)
    def __init__(self, new, row):
        super(Editor, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.new = new
        self.restoreGeometry(settings.value("Editor/windowGeo"))
        # setup texteditor and titleeditor, set window title
        if not new:
            self.datetime = row['datetime']
            self.titleEditor.setText(row['title'])
            formats = None if row['plaintext'] else nikki.getformat(row['id'])
            self.textEditor.setText(row['text'], formats)
        else:
            self.datetime = None
        self.textEditor.setFont(textfont)
        self.textEditor.setAutoIndent(int(settings.value(':/Editor/autoindent', 1)))
        self.titleEditor.setFont(titlefont)
        titlehint = (row['title'] if row else None) or \
                    (dt_trans(self.datetime,True) if self.datetime else None) or \
                    self.tr('New Diary')
        self.setWindowTitle("%s - Hazama" % titlehint)
        # setup datetime display
        self.dtLabel.setText('' if self.datetime is None
                             else dt_trans(self.datetime))
        self.dtLabel.setFont(datefont)
        self.dtBtn.setIcon(QIcon(':/editor/clock.png'))
        sz = min(dfontm.ascent(), 16)
        self.dtBtn.setIconSize(QSize(sz, sz))
        # set up tageditor
        self.updateTagEditorFont('')
        if not new: self.tagEditor.setText(row['tags'])
        completer = TagCompleter(nikki.gettag(), self)
        self.tagEditor.setCompleter(completer)
        self.timeModified = self.tagsModified = False
        # setup shortcuts
        self.closeSaveSc = QShortcut(QKeySequence.Save, self)
        self.closeSaveSc.activated.connect(self.close)
        self.closeSaveSc2 = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.closeSaveSc2.activated.connect(self.close)
        self.preSc = QShortcut(QKeySequence(Qt.CTRL+Qt.Key_PageUp), self)
        self.nextSc = QShortcut(QKeySequence(Qt.CTRL+Qt.Key_PageDown), self)

    def closeEvent(self, event):
        "Save geometry information and diary"
        settings.setValue('Editor/windowGeo', self.saveGeometry())
        nikkiid = self.saveNikki()
        event.accept()
        self.closed.emit(self.id, nikkiid, self.tagsModified)

    def closeNoSave(self):
        settings.setValue('Editor/windowGeo', self.saveGeometry())
        self.hide()
        self.deleteLater()
        self.closed.emit(self.id, -1, False)

    def saveNikki(self):
        "Save if changed and return nikkiid,else return -1"
        if (self.textEditor.document().isModified() or
        self.titleEditor.isModified() or self.timeModified or
        self.tagsModified):
            if self.datetime is None:
                self.datetime = currentdt_str()
            if self.tagsModified:
                tags = self.tagEditor.text().split()
                tags = list(filter(lambda t: tags.count(t)==1, tags))
            else:
                tags = None
            # realid: id returned by database
            realid = nikki.save(id=self.id, datetime=self.datetime,
                                html=self.textEditor.toHtml(),
                                plaintxt=self.textEditor.toPlainText(),
                                title=self.titleEditor.text(),
                                tags=tags, new=self.new)
            return realid
        else:
            return -1

    @Slot()
    def on_tagEditor_textEdited(self):
        # tageditor.isModified() will be reset by completer.So this instead.
        self.tagsModified = True

    @Slot()
    def on_dtBtn_clicked(self):
        dt = currentdt_str() if self.datetime is None else self.datetime
        new_dt = DateTimeDialog.getDateTime(dt, self)
        if new_dt is not None and new_dt!=self.datetime:
            self.datetime = new_dt
            self.dtLabel.setText(dt_trans(new_dt))
            self.timeModified = True

    def showEvent(self, event):
        if not int(settings.value('/Editor/titlefocus', 1)):
            self.textEditor.setFocus()
        self.textEditor.moveCursor(QTextCursor.Start)

    def updateTagEditorFont(self, text):
        "Set tagEditor's placeHoderFont to italic"
        fontstyle = 'normal' if text else 'italic'
        self.tagEditor.setStyleSheet('font-style: %s' % fontstyle)

    def setEditorId(self, id):
        self.id = id


class Main(QWidget):
    def __init__(self):
        super(Main, self).__init__()
        self.restoreGeometry(settings.value("Main/windowgeo"))
        self.setWindowTitle('Hazama Prototype Ver'+str(__version__))

        self.nlist = NList()
        self.nlist.load()
        self.tlist = TList()
        self.splitter = NSplitter()
        self.toolbar = QToolBar()
        self.searchbox = SearchBox()
        self.countlabel = QLabel()

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        self.searchbox.textChanged.connect(self.filter)
        self.nlist.needRefresh.connect(self.on_nlist_needRefresh)
        # setuo Splitter
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet('QSplitter::handle{background: rgb(181,61,0)}')
        self.splitter.addWidget(self.tlist)
        self.splitter.addWidget(self.nlist)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)
        tlist_w = int(settings.value('Main/taglistwidth', 0))
        self.splitter.setSizes([tlist_w, -1])

        # setup ToolBar
        self.creActs()  #create actions
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setStyleSheet('QToolBar{background: rgb(242, 241, 231);'
                                   'border-bottom: 1px solid rgb(181, 61, 0);'
                                   'padding: 2px; spacing: 2px}')
        self.sorAct.setMenu(SortOrderMenu(nlist=self.nlist))
        for a in [self.creAct, self.delAct, self.tlistAct, self.sorAct, self.cfgAct]:
            self.toolbar.addAction(a)
        #label
        self.countlabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.countlabel.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.countlabel.setIndent(6)
        self.countlabel.setStyleSheet('color: rgb(144, 144, 144)')
        self.updateCountLabel()
        self.toolbar.addWidget(self.countlabel)

        self.toolbar.addWidget(self.searchbox)
        self.searchbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        sortbtn = self.toolbar.widgetForAction(self.sorAct)
        sortbtn.setPopupMode(QToolButton.InstantPopup)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.splitter)
        self.setLayout(layout)
        if int(settings.value('Main/taglistvisible', 0)):
            self.tlistAct.trigger()
        else:
            self.tlist.hide()

    def closeEvent(self, event):
        settings.setValue('Main/windowgeo', self.saveGeometry())
        taglistvisible = self.tlist.isVisible()
        settings.setValue('Main/taglistvisible', int(taglistvisible))
        if taglistvisible:
            settings.setValue('Main/taglistwidth', self.splitter.sizes()[0])
        event.accept()
        qApp.quit()

    def filter(self, text=None):
        '''Connected to SearchBox and TagList.Argument "text" belongs to SearchBox'''
        text = self.searchbox.text() if text is None else text
        try:
            data = self.tlist.currentItem().data(1)
            tagid = None if data=='All' else data
        except AttributeError:  # TagList hidden
            tagid = None
        self.nlist.clear()
        self.nlist.load(tagid=tagid, search=text if text else None)

    def creActs(self):
        self.tlistAct = QAction(QIcon(':/images/tlist.png'), self.tr('Tag List'),
                                self, shortcut=QKeySequence(Qt.Key_F9))
        self.tlistAct.setCheckable(True)
        self.tlistAct.triggered[bool].connect(self.toggleTagList)
        self.creAct = QAction(QIcon(':/images/new.png'), self.tr('New'),
                              self, shortcut=QKeySequence.New,
                              triggered=self.nlist.newNikki)
        self.delAct = QAction(QIcon(':/images/delete.png'), self.tr('Delete'),
                              self, triggered=self.nlist.delNikki)
        self.sorAct = QAction(QIcon(':/images/sort.png'), self.tr('Sort By'), self)
        self.cfgAct = QAction(QIcon(':/images/config.png'), self.tr('Settings'),
                              self, triggered=self.startConfigDialog)

    def startConfigDialog(self):
        self.cfgdialog = ConfigDialog(self)
        self.cfgdialog.show()

    def toggleTagList(self, checked):
        lst = self.tlist
        lst.setVisible(checked)
        if checked:
            lst.load()
            lst.setCurrentRow(0)
            lst.itemSelectionChanged.connect(self.filter)
        else:
            # currentItem is None when tag deleted
            if lst.currentItem() is None or lst.currentRow()!=0:
                lst.setCurrentRow(0)  # reset filter
            # avoid refreshing nlist by unexpected signal
            lst.itemSelectionChanged.disconnect(self.filter)
            settings.setValue('Main/taglistwidth', self.splitter.sizes()[0])

    def showEvent(self, event):
        self.nlist.setFocus()

    def updateCountLabel(self):
        "Only called when diary saving or deleting"
        c = nikki.count()
        if c > 1: self.countlabel.setText(self.tr('%i diaries') % c)

    def on_nlist_reloaded(self):
        self.searchbox.clear()
        self.tlist.setCurrentRow(0)

    def on_nlist_needRefresh(self, label, tlist):
        if label: self.updateCountLabel()
        if tlist and self.tlist.isVisible(): self.tlist.load()


class TList(QListWidget):
    def __init__(self):
        super(TList, self).__init__()
        self.setItemDelegate(TListDelegate())
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setUniformItemSizes(True)
        self.setStyleSheet(TListDelegate.stylesheet)

    def load(self):
        logging.info('Tag List load')
        self.clear()  # this may emit unexpected signal when has selection
        all = QListWidgetItem(self)
        all.setData(1, 'All')
        for t in nikki.gettag(getcount=True):
            item = QListWidgetItem(self)
            item.setData(3, t[1])
            item.setData(2, t[2])
            item.setData(1, t[0])

    # all three events below for drag scroll
    def mousePressEvent(self, event):
        self.tracklst = []

    def mouseMoveEvent(self, event):
        if self.tracklst != None:
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


class ConfigDialog(QDialog, Ui_Settings):
    lang2index = {'en': 0, 'zh_CN': 1, 'ja': 2}  # index used in combo
    index2lang = {b: a for (a, b) in lang2index.items()}
    def __init__(self, parent=None):
        super(ConfigDialog, self).__init__(parent, Qt.WindowTitleHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.setFont(sysfont)

        self.aindCheck.setChecked(int(settings.value('Editor/autoindent', 1)))
        self.tfocusCheck.setChecked(int(settings.value('Editor/titlefocus', 0)))
        self.bkCheck.setChecked(int(settings.value('Main/backup', 1)))
        self.langCombo.setCurrentIndex(self.lang2index[
                                       settings.value('Main/lang', 'en')])

    def closeEvent(self, event):
        del main.cfgdialog
        event.accept()

    def accept(self):
        settings.setValue('Editor/autoindent', int(self.aindCheck.isChecked()))
        settings.setValue('Editor/titlefocus', int(self.tfocusCheck.isChecked()))
        settings.setValue('Main/backup', int(self.bkCheck.isChecked()))
        lang = self.index2lang[self.langCombo.currentIndex()]
        if settings.value('Main/lang') != lang:
            settings.setValue('Main/lang', lang)
            set_trans(settings)
            restart_main()
        logging.info('Settings saved')
        try:
            super(ConfigDialog, self).accept()
        except RuntimeError:
            # main.cfgdialog has been deleted after restart_main
            pass

    @Slot()
    def on_exportBtn_clicked(self):
        export_all = not bool(self.exportOption.currentIndex())
        txtpath, type = QFileDialog.getSaveFileName(self,
            self.tr('Export Diary'), os.getcwd(),
            self.tr('Plain Text (*.txt);;Rich Text (*.rtf)'))

        if txtpath == '': return    # dialog canceled
        if type.endswith('txt)'):
            selected = (None if export_all else
                        [i.data(2) for i in main.nlist.selectedItems()])
            nikki.exporttxt(txtpath, selected)



if __name__ == '__main__':
    program_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(program_path)

    timee = time.clock()
    app = QApplication(sys.argv)
    appicon = QIcon(':/appicon16.png')
    appicon.addFile(':/appicon32.png')
    appicon.addFile(':/appicon64.png')
    app.setWindowIcon(appicon)
    settings = QSettings('config.ini', QSettings.IniFormat)
    settings.setIniCodec('UTF-8')
    set_trans(settings)
    dt_trans = dt_trans_gen()

    # setup fonts
    titlefont = QFont()
    titlefont.fromString(settings.value('/Font/title'))
    ttfontm = QFontMetrics(titlefont)
    datefont = QFont()
    datefont.fromString(settings.value('/Font/datetime'))
    dfontm = QFontMetrics(datefont)
    textfont = QFont()
    textfont.fromString(settings.value('/Font/text'))
    sysfont = app.font()
    if settings.value('/Font/default'):
        defont = QFont()
        defont.fromString(settings.value('/Font/default'))
        app.setFont(defont)
    else:
        defont = sysfont
    defontm = QFontMetrics(defont)

    logging.basicConfig(level=logging.DEBUG)
    dbpath = settings.value('/Main/dbpath', 'nikkichou.db')
    nikki = Nikki(dbpath)
    logging.info(str(nikki))

    main = Main()
    main.show()
    logging.debug('startup take %s seconds' % round(time.clock()-timee,3))
    if int(settings.value('Main/backup', 1)): backupcheck(dbpath)
    sys.exit(app.exec_())
