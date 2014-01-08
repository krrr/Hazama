from PySide.QtGui import *
from PySide.QtCore import *
import sys, os
from db import Nikki
import configparser
import time
import logging

__version__ = 0.03
# from config tile
titlefont = QFont('SimSun')
titlefont.setBold(True)
titlefont.setPixelSize(12)
datefont = QFont('Segoe UI')
datefont.setPixelSize(12)
dfontm = QFontMetrics(datefont)
textfont = QFont('SimSun')  # WenQuanYi Micro Hei
textfont.setPixelSize(13)
txfontm = QFontMetrics(textfont)
defaultfont = QFont('Microsoft YaHei')
defaultfont.setPixelSize(12)
defontm = QFontMetrics(defaultfont)

if os.sep not in sys.argv[0]:
    path = ''
else:
    path = os.path.split(sys.argv[0])[0] + os.sep


class CintaNListDelegate(QStyledItemDelegate):
    "CintaNotes like delegate for Entry(QListWidgetItem)"
    def __init__(self):
        "calculate first"
        super(CintaNListDelegate, self).__init__()

        self.tr_h = titlefont.pixelSize() + 11

        leading = txfontm.leading() if (txfontm.leading() >= 0) else 0
        self.text_h = (txfontm.height()+leading) * \
                      int(settings.value('Nlist/previewlines', 4))
        self.dico_w, self.dico_h = 8, 7
        self.dico_y = self.tr_h // 2 - 3
        # for displaying text
        self.qtd = NTextDocument()
        self.qtd.setDefaultFont(textfont)
        self.qtd.setUndoRedoEnabled(False)
        self.qtd.setDocumentMargin(0)

    def paint(self, painter, option, index):
        x, y, w= option.rect.x()+1, option.rect.y(), option.rect.width()-3
        row = index.data()

        selected = bool(option.state & QStyle.State_Selected)
        areafocused = bool(option.state & QStyle.State_Active)
        is_current = bool(option.state&QStyle.State_HasFocus) and areafocused
        
        mainrect = QRect(x, y, w, self.height)
        painter.setPen(QColor(180, 180, 180))
        painter.setBrush(QColor(255, 255, 255))
        painter.drawRect(mainrect)

        # titlerect and title
        painter.setFont(titlefont)
        titlerect = QRect(x+1, y+1, w-1, self.tr_h)
        painter.setPen(Qt.NoPen)
        if selected:
            painter.setBrush(QColor(251, 225, 184) if areafocused \
                             else QColor(251, 230, 195))
        else:
            painter.setBrush(QColor(254, 250, 244))
        painter.drawRect(titlerect)
        painter.setPen(QColor(150, 118, 64) if selected
                       else QColor(121, 107, 85))
        painter.drawText(x+8, y+1, w-100, self.tr_h,
                         Qt.AlignLeft|Qt.AlignVCenter, row['title'])

        # border change
        if selected:
            imainrect = QRect(x+1, y+1, w-2, self.height-2)

            painter.setBrush(Qt.NoBrush)
            painter.setPen(QColor(183, 161, 135) if is_current
                           else QColor(180, 180, 180))
            painter.drawRect(mainrect)
            painter.setPen(QColor(172, 158, 134))
            painter.drawRect(imainrect)

            if is_current:
                pen = QPen()
                pen.setDashPattern([1,1,1,1,1,1])
                pen.setColor(QColor(23, 7, 121))
                painter.setPen(pen)
                painter.drawRect(mainrect)
                
                pen.setDashPattern([1,1,1,1])
                pen.setColor(QColor(93, 73, 57))
                painter.setPen(pen)
                painter.drawRect(imainrect)

        # date with icon
        painter.setFont(datefont)
        date_w = dfontm.width(row['created'])
        date_x = w-date_w-9
        painter.drawText(date_x, y+1, date_w, self.tr_h,
                         Qt.AlignVCenter, row['created'])
        painter.setBrush(Qt.NoBrush)
        dico = QRect(date_x-self.dico_w-4,
                     y+self.dico_y, self.dico_w, self.dico_h)
        painter.setPen(QColor(208,186,149) if selected
                       else QColor(198,198,198))
        painter.drawRoundedRect(dico, 1, 1)
        dicop_x = date_x-self.dico_h/2 - 4
        dicocenter_y = y + self.dico_y + 4
        painter.setPen(QColor(191,173,143))
        painter.drawLine(dicop_x, y+self.dico_y+2, dicop_x, dicocenter_y)
        painter.drawLine(dicop_x, dicocenter_y, dicop_x+2, dicocenter_y)

        # text
        painter.setPen(QColor(0,0,0))
        painter.save()
        self.qtd.setText(row['text'], row['plaintext'], row['id'])
        self.qtd.setTextWidth(w-22)
        painter.translate(x+12, y+self.tr_h+self.tag_h+2)
        self.qtd.drawContents(painter, QRectF(0, 0, w-21, self.text_h))
        painter.restore()

        # tags
        if self.tag_h:
            painter.setPen(QColor(161, 151, 136))
            painter.setFont(defaultfont)
            painter.drawText(x+16, y+self.tr_h+3, 
                             200, 30, Qt.AlignLeft, row['tags'])

    def sizeHint(self, option, index):
        self.tag_h = 20 if index.data()['tags'] else 0
        self.height = self.tag_h + self.text_h + self.tr_h + 10
        
        return QSize(-1, self.height+1)


class CintaTListDelegate(QStyledItemDelegate):
    def __init__(self):
        super(CintaTListDelegate, self).__init__()
        self.h = defaultfont.pixelSize()+8
    def paint(self, painter, option, index):
        x, y, w= option.rect.x(), option.rect.y(), option.rect.width()
        tag, count = index.data().split()
        painter.setFont(defaultfont)
        
        selected = bool(option.state & QStyle.State_Selected)
        if index.row() == 0:
            pass
        else:
            painter.setPen(QColor(181,188,199))
            painter.drawLine(x+1, y, w-4, y)
            if selected:
                trect = QRect(x+5, y, w-7, self.h-1)
                painter.setPen(QColor(144,144,140))
                painter.setBrush(QColor(250, 250, 250))
                painter.drawRect(trect)
            
            # draw tag
            painter.setPen(QColor(20,20,20) if selected else 
                           QColor(100,100,115))
            textarea = QRect(x+10, y, w-15, self.h-1)
            tag = defontm.elidedText(tag, Qt.ElideRight, w-40)
            painter.drawText(textarea, Qt.AlignVCenter|Qt.AlignLeft, tag)
            # draw tag count
            painter.setFont(datefont)
            painter.setPen(QColor(20,20,20) if selected else 
                           QColor(181,188,199))
            painter.drawText(textarea, Qt.AlignVCenter|Qt.AlignRight, count)
            
            
        # painter.drawText(option.rect, tag)
        
    def sizeHint(self, option, index):
        h = self.h if index.row() else self.h*1.2
        return QSize(-1, h)


class Entry(QListWidgetItem):
    def __init__(self, row, parent=None):
        super(Entry, self).__init__(parent)
        self.setData(2, row)


class NList(QListWidget):
    def __init__(self):
        super(NList, self).__init__()
        self.setMinimumSize(350,200)
        self.editors = {}

        self.setSelectionMode(self.ExtendedSelection)
        self.itemDoubleClicked.connect(self.starteditor)
        
        self.setItemDelegate(CintaNListDelegate())
        self.setStyleSheet('QListWidget{background-color: rgb(173,179,180); \
                           border: solid 0px}')
        
        # Context Menu
        self.editAct = QAction('Edit', self,
                                shortcut=QKeySequence('Return'),
                                triggered=self.starteditor)
        self.addAction(self.editAct)  # make shortcut working anytime
        self.delAct = QAction('Delete', self, shortcut=QKeySequence('Delete'),
                              triggered=self.delNikki)
        self.addAction(self.delAct)
        self.newAct = QAction('New Nikki', self, shortcut=QKeySequence.New,
                              triggered=self.newNikki)
        self.addAction(self.newAct)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction(self.editAct)
        menu.addAction(self.delAct)
        menu.addSeparator()
        menu.addAction(self.newAct)
        
        selcount = len(self.selectedItems())
        self.editAct.setDisabled(True if (selcount>1 or selcount==0)
                                 else False)
        self.delAct.setDisabled(True if selcount==0 else False)
        menu.popup(event.globalPos())

    def starteditor(self, item=None, new=False):
        if not new:
            # called by doubleclick event or contextmenu
            self.curtitem = item if item else self.selectedItems()[0] 
            row = self.curtitem.data(2)
            editor = Editwindow(new=False, row=row, nlist=self)
            self.editors[row['id']] = editor
        else:
            editor = Editwindow(new=True, row=None, nlist=self)
            self.editors[None] = editor

        center = main.geometry().center()
        w, h = (int(i) for i in settings.value('Editor/size', (500, 400)))
        editor.setGeometry(center.x()-w/2, center.y()-h/2, w, h)

        editor.show()

    def delNikki(self):
        msgbox = QMessageBox(QMessageBox.NoIcon,
                             'Confirm',
                             'Delete it?',
                             QMessageBox.Yes|QMessageBox.Cancel,
                             parent=self)
        msgbox.setDefaultButton(QMessageBox.Cancel)
        ret = msgbox.exec_()

        if ret == QMessageBox.Yes:
            for i in self.selectedItems():
                nikki.delete(i.data(2)['id'])
                self.takeItem(self.row(i))

    def newNikki(self):
        self.starteditor(None, True)

    def load(self):
        order = settings.value('NList/sortorder', 'created')
        for e in nikki.sorted(order):
            Entry(e, self)
        
        self.setCurrentRow(0)

    def refresh(self, id):
        logging.info('Nikki List reloading')
        self.clear()
        order = settings.value('NList/sortorder', 'created')
        for e in nikki.sorted(order):
            if e['id'] == id:
                rownum = self.count()
            Entry(e, self)

        self.setCurrentRow(rownum)

    def destroyEditor(self, editor):
        del self.editors[editor.id]


class Editwindow(QWidget):
    createdModified = False
    tagsModified = False
    def __init__(self, new, row, nlist):
        super(Editwindow, self).__init__()
        self.nlist = nlist

        self.setMinimumSize(350,200)

        self.titleeditor = QLineEdit(self)
        self.titleeditor.setFont(titlefont)
        # load data & set up nikki editor
        if not new:  # existing nikki
            self.id = row['id']
            self.created = row['created']
            self.modified = row['modified']
            self.titleeditor.setText(row['title'])
            self.editor = NTextEdit(row['text'],
                                    row['plaintext'],
                                    row['id'],
                                    parent=self)
        else:
            self.modified = self.created = self.id = None
            self.editor = NTextEdit(parent=self)
        
        titlehint = (row['title'] if row else None) or \
                    (self.created.split()[0] if self.created else None) or \
                    'New Nikki'
        self.setWindowTitle("%s - Hazama" % titlehint)
        
        
        # set up tageditor 
        self.tageditor = QLineEdit(self)
        self.tageditor.setPlaceholderText('Tags')
        if not new: self.tageditor.setText(row['tags'])
        self.tageditor.setFont(defaultfont)
        completer = TagCompleter(nikki.gettag(), self)
        self.tageditor.setCompleter(completer)
        self.tageditor.textChanged.connect(self.setTagsModified)
        
        self.title_h = self.titleeditor.sizeHint().height()
        self.tageditor_h = self.tageditor.sizeHint().height()
        self.box = QDialogButtonBox(QDialogButtonBox.Save | \
                                    QDialogButtonBox.Cancel,
                                    parent=self)
        self.box.accepted.connect(self.close)
        self.box.rejected.connect(self.hide)
        self.box_w, self.box_h = self.box.sizeHint().toTuple()
        # title and created,modified,tags
        # self.d_created = NDate(self.created, self)
        # self.d_created.move(50, 330)
        # self.d_created.dateTimeChanged.connect(self.setCreatedModified)
        
            
    def closeEvent(self, event):
        if (self.editor.document().isModified() or
        self.titleeditor.isModified() or self.createdModified or
        self.tagsModified):
            realid = self.saveNikki()
            self.nlist.refresh(realid)
        settings.setValue('Editor/size', self.size().toTuple())
        event.accept()
        self.nlist.destroyEditor(self)

    def saveNikki(self):
        if not self.created:  # new nikki
            self.created = time.strftime('%Y/%m/%d %H:%M')
            modified = self.created
        else:
            modified = time.strftime('%Y/%m/%d %H:%M')
        tags = self.tageditor.text().split() if self.tagsModified else None
        # realid: id returned by database
        realid = nikki.save(self.id, self.created, modified,
                            self.editor.toHtml(), self.titleeditor.text(),
                            tags)
        return realid
    # def setCreatedModified(self):
        # self.created = self.d_created.toString()
        # self.createdModified = True
    def setTagsModified(self):
        # tageditor.isModified() will be reset by completer.So this instead.
        self.tagsModified = True

    def paintEvent(self, event):
        w, h = self.size().toTuple()
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(247, 241, 231))  # 199,199,233
        daterect = QRect(0, h-self.box_h-20, w, self.box_h+20)
        painter.drawRect(daterect)
        
        painter.setBrush(QColor(249,245,238))  # 77,199,145
        painter.drawRect(0, h-self.box_h-70, w, 50)
        
        painter.setPen(QColor(115,115,115))
        painter.setFont(datefont)
        date = '   Created:%s\n   Modified:%s' % (self.created, self.modified)
        painter.drawText(daterect,Qt.AlignVCenter, date)

    def resizeEvent(self, event):
        w, h = event.size().toTuple()
        # from buttom to top
        box_x, box_y = w-self.box_w-10, h-self.box_h-10
        self.box.move(box_x, box_y)
        self.tageditor.setGeometry(20, box_y-35, w-40, self.tageditor_h)
        self.editor.setGeometry(0, self.title_h, w, box_y-60)
        self.titleeditor.resize(w, self.title_h)

    def showEvent(self, event):
        self.editor.setFocus()
        self.editor.moveCursor(QTextCursor.Start)


class TagCompleter(QCompleter):
    def __init__(self, tagL, parent=None):
        self.tagL = tagL
        super(TagCompleter, self).__init__(tagL, parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        
    def pathFromIndex(self, index):
        # path is current matched tag.
        path = QCompleter.pathFromIndex(self, index)
        # a list like [tag1, tag2, tag3(maybe a part)]
        L = self.widget().text().split()
        if len(L) > 1:
            path = '%s %s ' % (' '.join(L[:-1]), path)
        else:
            path += ' '
        return path

    def splitPath(self, path):
        # path is tag string like "tag1 tag2 tag3(maybe a part) "
        path = path.split()[-1] if path.split() else None
        if (path in self.tagL) or (path == None):
            return ' '
        else:
            return [path,]


class NTextEdit(QTextEdit):
    def __init__(self, *values, parent=None):
        super(NTextEdit, self).__init__(parent)
        self.setTabChangesFocus(True)
        self.autoIndent = int(settings.value('Editor/autoindent', 0))
        
        doc = NTextDocument()
        doc.setDefaultFont(textfont)
        if values:  # Edit existing nikki
            text, plain, nikkiid = values
            doc.setText(text, plain, nikkiid)
        self.setDocument(doc)
            
        prt = self.palette()
        prt.setColor(prt.Highlight, QColor(180, 180, 180))
        prt.setColor(prt.HighlightedText, QColor(0, 0, 0))
        self.setPalette(prt)

        self.creatacts()
        self.setModified(False)

    def creatacts(self):
        self.submenu = QMenu('Format')
        self.hlAct = QAction('Highlight', self, shortcut=QKeySequence('Ctrl+H'))
        self.soAct = QAction('Strike out', self, shortcut=QKeySequence('Ctrl+-'))
        self.bdAct = QAction('Bold', self, shortcut=QKeySequence('Ctrl+B'))
        self.ulAct = QAction('Underline', self, shortcut=QKeySequence('Ctrl+U'))
        self.itaAct = QAction('Italic', self, shortcut=QKeySequence('Ctrl+I'))

        self.hlAct.triggered.connect(self.setHL)
        self.soAct.triggered.connect(self.setSO)
        self.bdAct.triggered.connect(self.setBD)
        self.ulAct.triggered.connect(self.setUL)
        self.itaAct.triggered.connect(self.setIta)

        for a in (self.hlAct, self.bdAct, self.soAct, self.bdAct,
                  self.ulAct, self.itaAct):
            self.addAction(a)
            self.submenu.addAction(a)
            a.setCheckable(True)

        self.submenu.addSeparator()
        self.clrAct = QAction('Clear format', self,
                              shortcut=QKeySequence('Ctrl+D'))
        self.addAction(self.clrAct)
        self.submenu.addAction(self.clrAct)
        self.clrAct.triggered.connect(self.clearformat)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu(event.globalPos())
        before = menu.actions()[2]

        curtfmt = self.currentCharFormat()
        self.hlAct.setChecked(True if curtfmt.background().color() == \
                              QColor(255, 250, 160) else False)
        self.bdAct.setChecked(True if curtfmt.fontWeight() == QFont.Bold \
                              else False)
        self.soAct.setChecked(curtfmt.fontStrikeOut())    
        self.ulAct.setChecked(curtfmt.fontUnderline())   
        self.itaAct.setChecked(curtfmt.fontItalic())

        menu.insertSeparator(before)        
        menu.insertMenu(before, self.submenu)
        menu.exec_(event.globalPos())

    def setHL(self, pre=None):
        if pre:
            hasFormat = False
        else:
            curtfmt = self.currentCharFormat()
            hasFormat = curtfmt.background().color() == \
                        QColor(255, 250, 160)
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(QColor('white') if hasFormat
                                 else QColor(255, 250, 160)))
        self.textCursor().mergeCharFormat(fmt)

    def setBD(self, pre=None):
        if pre:
            hasFormat = False
        else:
            curtfmt = self.currentCharFormat()
            hasFormat = (curtfmt.fontWeight() == QFont.Bold)
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Normal if hasFormat else QFont.Bold)
        self.textCursor().mergeCharFormat(fmt)

    def setSO(self, pre=None):
        if pre:
            hasFormat = False
        else:
            curtfmt = self.currentCharFormat()
            hasFormat = curtfmt.fontStrikeOut()
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(not hasFormat)
        self.textCursor().mergeCharFormat(fmt)

    def setUL(self, pre=None):
        if pre:
            hasFormat = False
        else:
            curtfmt = self.currentCharFormat()
            hasFormat = curtfmt.fontUnderline()
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not hasFormat)
        self.textCursor().mergeCharFormat(fmt)

    def setIta(self, pre=None):
        if pre:
            hasFormat = False
        else:
            curtfmt = self.currentCharFormat()
            hasFormat = curtfmt.fontItalic()
        fmt = QTextCharFormat()
        fmt.setFontItalic(not hasFormat)
        self.textCursor().mergeCharFormat(fmt)

    def clearformat(self):
        fmt = QTextCharFormat()
        self.textCursor().setCharFormat(fmt)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and self.autoIndent:
            spacecount = 0
            cur = self.textCursor()
            savedpos = cur.position()
            cur.movePosition(QTextCursor.StartOfBlock)
            cur.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            while cur.selectedText() == ' ':
                spacecount += 1
                cur.clearSelection()
                cur.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            
            cur.setPosition(savedpos)
            super(NTextEdit, self).keyPressEvent(event)
            cur.insertText(' '*spacecount)
        else:
            return super(NTextEdit, self).keyPressEvent(event)

    def currentCharFormat(self):
        "Solve right-to-left(cursor at left,anchor at right) selection"
        cur = self.textCursor()
        cpos, apos = cur.position(), cur.anchor()
        if cpos >= apos:  # Normal case
            return cur.charFormat()
        else:  # Now it is like CxxxxxA  (x represents characters)
            cur.clearSelection()
            cur.setPosition(apos, QTextCursor.KeepAnchor)
            return cur.charFormat()
            
    def insertFromMimeData(self, source):
        "Disable some unsuportted types"
        self.insertHtml(source.html())


class NTextDocument(QTextDocument):
    typedic = {1: 'setBD', 2: 'setHL', 3: 'setIta', 4: 'setSO', 5: 'setUL'}
    def setText(self, text, plain, nikkiid=None):
        self.setPlainText(text)
        if not plain:
            self.cur = QTextCursor(self)
            for r in nikki.getformat(nikkiid):
                self.cur.setPosition(r[0])
                self.cur.setPosition(r[0]+r[1], mode=self.cur.KeepAnchor)
                richfunc = getattr(NTextEdit, self.typedic[r[2]])
                richfunc(self, True)

    def textCursor(self):
        "Make NTextEdit.setXX use NTextDocument.cur as textCursor"
        return self.cur


class NDate(QDateTimeEdit):
    fmt = "yyyy/MM/dd HH:mm"
    def __init__(self, string, parent=None):
        dt = QDateTime.fromString(string, self.fmt)
        super(NDate, self).__init__(dt, parent)
        self.setDisplayFormat(self.fmt)
        
    def toString(self):
        return self.dateTime().toString(self.fmt)


class Main(QWidget):
    def __init__(self):
        super(Main, self).__init__()
        self.restoreGeometry(settings.value("Main/windowGeo"))
        self.setWindowTitle('Hazama Prototype Ver0.03')
        
        self.nlist = NList()
        self.nlist.load()
        
        layout = QVBoxLayout()
        self.splitter = MainSplitter()
        layout.setContentsMargins(0,0,0,0)
        self.splitter.splitterMoved.connect(self.keepTList)
        layout.setSpacing(0)
        self.splitter.addWidget(TList())
        self.splitter.addWidget(self.nlist)
        for i in range(2):
            self.splitter.setCollapsible(i, False)
        layout.addWidget(self.splitter)
        self.setLayout(layout)
        self.keepTList(init=True)

    def closeEvent(self, event):
        settings.setValue('Main/windowGeo', self.saveGeometry())
        settings.setValue('Main/TListWidth', self.splitter.sizes()[0])
        event.accept()

    def keepTList(self, pos=None, index=None, init=False):
        "keep TList's size when reducing window's width"
        if init:
            self.setMinimumWidth(int(settings.value('Main/TListWidth'))+350+2)
        else:
            self.setMinimumWidth(pos+350+2)


class TList(QListWidget):
    def __init__(self, parent=None):
        super(TList, self).__init__(parent)
        self.setItemDelegate(CintaTListDelegate())
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setStyleSheet('QListWidget{background-color: rgb(227,235,249);'
                           'border: solid 0px}')
        self.itemClicked.connect(self.clicked)
        QListWidgetItem('All all', self) 
        for t in nikki.gettag(getcount=True):
            QListWidgetItem(t[0]+' '+str(t[1]), self)

    def clicked(self, item):
        tag = item.data(0).split()[0]
      
    # three events for drag scroll
    def mousePressEvent(self, event):
        self.tracklst = []

    def mouseMoveEvent(self, event):
        if self.tracklst != None:
            self.tracklst.append(event.pos().y())
            if len(self.tracklst) > 4:
                change = self.tracklst[-1] - self.tracklst[0]
                scrollbar = self.verticalScrollBar()
                scrollbar.setValue(scrollbar.value() - change)

    def mouseReleaseEvent(self, event):
        if self.tracklst != None:
            if len(self.tracklst) <= 4:  # haven't moved
                pevent = QMouseEvent(QEvent.MouseButtonPress, event.pos(),
                                    event.globalPos(), Qt.LeftButton,
                                    Qt.LeftButton, Qt.NoModifier)
                QListWidget.mousePressEvent(self, pevent)

        self.tracklst = None


class MainSplitter(QSplitter):
    def __init__(self, parent=None):
        super(MainSplitter, self).__init__(parent)
        self.setHandleWidth(2)
        
    def resizeEvent(self, event):
        # reference: stackoverflow.com/questions/14397653
        if event.oldSize().width() != -1:
            TListWidth = self.sizes()[0]
            self.setSizes([TListWidth, event.size().width()-2-TListWidth])
        else:
            # init, set taglist to saved size
            w = int(settings.value('Main/TListWidth', 0))
            self.setSizes([w, event.size().width()-2-w])
    
    def createHandle(self):
        handle = QSplitterHandle(Qt.Horizontal, self)
        handle.setStyleSheet('background-color: rgb(227,235,249)') 
        handle.setCursor(Qt.SizeHorCursor)
        return handle



 
if __name__ == '__main__':
    print('ハザマ：今日はいい天気ですね。起動中です。')
    
    logging.basicConfig(level=logging.DEBUG)
    timee = time.clock()
    settings = QSettings(path+'config.ini', QSettings.IniFormat)
    app = QApplication(sys.argv)
    
    nikki = Nikki(path + 'test.db')
    logging.info(str(nikki))
    main = Main()


    main.show()
    logging.debug('startup take %s seconds' % round(time.clock()-timee,3))
    
    sys.exit(app.exec_())
