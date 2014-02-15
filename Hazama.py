from PySide.QtGui import *
from PySide.QtCore import *
import res
import ui.configdialog
from db import Nikki

import sys, os
import socket
import configparser
import time
import logging

__version__ = 0.06


if os.sep not in sys.argv[0]:
    path = ''
else:
    path = os.path.split(sys.argv[0])[0] + os.sep


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
        trans.load('lang/'+lang, directory=path)
        transQt = QTranslator()
        transQt.load('qt_'+lang, QLibraryInfo.location(QLibraryInfo.TranslationsPath))
        for i in [trans, transQt]: qApp.installTranslator(i)


class NFont(QFont):
    '''Calculate pixelSize when font set by pointSize.'''
    def __init__(self, *args, s=None):
        super(NFont, self).__init__(*args)
        if s: self.fromString(s)
        w = QWidget()
        self.DPI = w.logicalDpiY()

    def pixelSize(self):
        return int(self.pointSize() / 72 * self.DPI) - 1


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
        x, y, w= option.rect.x(), option.rect.y(), option.rect.width()-2
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
        painter.drawText(x+8, y+1, w-150, self.tr_h,
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
                pen.setDashPattern([1, 1, 1, 1, 1, 1])
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
        painter.setPen(QColor(208, 186, 149) if selected
                       else QColor(198, 198, 198))
        painter.drawRoundedRect(dico, 1, 1)
        dicop_x = date_x-self.dico_h/2 - 4
        dicocenter_y = y + self.dico_y + 4
        painter.setPen(QColor(191, 173, 143))
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


class TListDelegate(QStyledItemDelegate):
    '''Default TagList(TList) Delegate.Also contains TList's stylesheet'''
    TListSS = ('QListWidget{background-color: rgb(234,182,138);'
               'border: solid 0px}')
    def __init__(self):
        super(TListDelegate, self).__init__()
        self.h = defaultfont.pixelSize()+8

    def paint(self, painter, option, index):
        x, y, w= option.rect.x(), option.rect.y(), option.rect.width()
        tag, count = index.data(3), str(index.data(2))
        painter.setFont(defaultfont)

        selected = bool(option.state & QStyle.State_Selected)

        if index.row() == 0:  # row 0 is always All(clear tag filter)
            painter.setPen(QColor(80, 80, 80))
            painter.drawText(x+4, y+1, w-8, self.h-1,
                             Qt.AlignLeft|Qt.AlignLeft,
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
            textarea = QRect(x+4, y, w-8, self.h)
            tag = defontm.elidedText(tag, Qt.ElideRight, w-dfontm.width(count)-12)
            painter.drawText(textarea, Qt.AlignVCenter|Qt.AlignLeft, tag)
            # draw tag count
            painter.setFont(datefont)
            painter.drawText(textarea, Qt.AlignVCenter|Qt.AlignRight, count)

    def sizeHint(self, option, index):
        return QSize(-1, self.h)


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
        self.setStyleSheet('QListWidget{background-color: rgb(173,179,180);'
                           'border: solid 0px}')

        # Context Menu
        self.editAct = QAction(self.tr('Edit'), self,
                                shortcut=QKeySequence('Return'),
                                triggered=self.starteditor)
        self.addAction(self.editAct)  # make shortcut working anytime
        self.delAct = QAction(self.tr('Delete'), self, shortcut=QKeySequence.Delete,
                              triggered=self.delNikki)
        self.addAction(self.delAct)
        self.selAct = QAction(self.tr('Select All'), self, shortcut=QKeySequence.SelectAll,
                              triggered=self.selectAll)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction(self.editAct)
        menu.addAction(self.delAct)
        menu.addSeparator()
        menu.addAction(self.selAct)

        selcount = len(self.selectedItems())
        self.editAct.setDisabled(True if (selcount>1 or selcount==0)
                                 else False)
        self.delAct.setDisabled(True if selcount==0 else False)
        menu.popup(event.globalPos())

    def starteditor(self, item=None, new=False):
        if not new:
            # called by doubleclick event or contextmenu or key-shortcut
            self.curtitem = item if item else self.selectedItems()[0]
            row = self.curtitem.data(2)
            id = row['id']
            if id in self.editors:
                self.editors[id].activateWindow()
            else:  # create new editor
                editor = Editor(new=False, row=row)
                self.editors[id] = editor
                editor.show()
        else:
            if None in self.editors:
                self.editors[None].activateWindow()
            else:  # create new editor
                editor = Editor(new=True, row=None)
                self.editors[None] = editor
                editor.show()

    def delNikki(self):
        msgbox = QMessageBox(QMessageBox.NoIcon,
                             self.tr('Delete Diary'),
                             self.tr('Are you sure you want to delete'
                                     'the selected diary?'),
                             QMessageBox.Yes|QMessageBox.No,
                             parent=self)
        msgbox.setDefaultButton(QMessageBox.Cancel)
        ret = msgbox.exec_()

        if ret == QMessageBox.Yes:
            for i in self.selectedItems():
                nikki.delete(i.data(2)['id'])
                self.takeItem(self.row(i))
            if main.tlist.isVisible(): self.main.tlist.load()
            main.updateCountLabel()

        # QWidget.destroy() doesn't work
        msgbox.deleteLater()

    def newNikki(self):
        self.starteditor(None, True)

    def load(self, *, tagid=None, search=None):
        order, reverse = self.getOrder()
        for e in nikki.sorted(order, reverse, tagid=tagid, search=search):
            Entry(e, self)

        self.setCurrentRow(0)

    def reload(self, id):
        order, reverse = self.getOrder()
        logging.info('Nikki List reload')
        self.clear()
        for e in nikki.sorted(order, reverse):
            if e['id'] == id:
                rownum = self.count()
            Entry(e, self)

        main.searchbox.clear()
        main.tlist.setCurrentRow(0)
        self.setCurrentRow(rownum)

    def getOrder(self):
        "get sort order(str) and reverse(int) from settings file"
        order = settings.value('NList/sortOrder', 'created')
        reverse = int(settings.value('NList/sortReverse', 1))
        return order, reverse


class Editor(QWidget):
    "Editor Window.Edit diary's contents,title,tag,modified time here."
    def __init__(self, new, row):
        super(Editor, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setMinimumSize(350,200)
        # setup window geometry
        if int(settings.value("Editor/centeropen", 0)):
            center = main.geometry().center()
            w, h = (int(i) for i in settings.value('Editor/size', (500, 400)))
            self.setGeometry(center.x()-w/2, center.y()-h/2, w, h)
        else:
            self.restoreGeometry(settings.value("Editor/windowGeo"))

        self.titleeditor = QLineEdit(self)
        self.titleeditor.setFont(titlefont)
        # load data & set up nikki editor
        if not new:  # existing nikki
            self.id = row['id']
            self.created = row['created']
            self.modified = row['modified']  # is '' when not modified
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
                    self.tr('New Diary')
        self.setWindowTitle("%s - Hazama" % titlehint)

        # setup timelabel(display created,modified datetime)
        cre = self.created if self.created is not None else ''
        mod = self.modified if self.modified is not None else ''
        datetime = self.tr('Created: %s\nModified: %s') % (cre, mod)
        self.timelabel = QLabel(datetime, self)
        self.timelabel.setFont(datefont)
        self.timelabel.setStyleSheet('color: rgb(115, 115, 115)')
        self.timelabel.mouseReleaseEvent = self.startTimeEditor
        self.timelabel_w = self.timelabel.sizeHint().width()
        # set up tageditor 
        self.tageditor = QLineEdit(self)
        self.tageditor.setPlaceholderText(self.tr('Tags separated by space'))
        self.tageditor.textChanged.connect(self.updateTagEditorFont)
        self.updateTagEditorFont('')
        if not new: self.tageditor.setText(row['tags'])
        self.tageditor.setFont(defaultfont)
        completer = TagCompleter(nikki.gettag(), self)
        self.tageditor.setCompleter(completer)
        self.tageditor.textChanged.connect(self.setTagsModified)
        # setup dialog buttons
        self.box = QDialogButtonBox(QDialogButtonBox.Save | \
                                    QDialogButtonBox.Cancel,
                                    parent=self)
        self.box.accepted.connect(self.close)
        self.box.rejected.connect(self.closeWithoutSaving)
        self.box_w, self.box_h = self.box.sizeHint().toTuple()

        self.title_h = self.titleeditor.sizeHint().height()
        self.tageditor_h = self.tageditor.sizeHint().height()
        self.timeModified = self.tagsModified = False

    def closeEvent(self, event):
        "Save geometry information and diary(if changed)"
        if int(settings.value('Editor/centeropen', 0)):
            settings.setValue('Editor/size', self.size().toTuple())
        else:
            settings.setValue('Editor/windowGeo', self.saveGeometry())
        self.saveNikki()
        event.accept()
        del main.nlist.editors[self.id]

    def closeWithoutSaving(self):
        self.hide()
        self.deleteLater()
        del main.nlist.editors[self.id]

    def saveNikki(self):
        "Save when necessary;Refresh NList and TList when necessary"
        if (self.editor.document().isModified() or
        self.titleeditor.isModified() or self.timeModified or
        self.tagsModified):
            if not self.created:  # new nikki
                self.created = time.strftime('%Y/%m/%d %H:%M')
                modified = ''
            else:
                modified = time.strftime('%Y/%m/%d %H:%M')
            tagsL = self.tageditor.text().split() if self.tagsModified else None
            tags = filter(lambda t: tagsL.count(t)==1, tagsL) if tagsL else None
            # realid: id returned by database
            realid = nikki.save(self.id, self.created, modified,
                                self.editor.toHtml(), self.titleeditor.text(),
                                tags)
            if realid is not None:  # save existed diary
                main.nlist.reload(realid)
                main.updateCountLabel()

        if self.tagsModified and main.tlist.isVisible():
            main.tlist.load()

    def setTagsModified(self):
        # tageditor.isModified() will be reset by completer.So this instead.
        self.tagsModified = True

    def paintEvent(self, event):
        w, h = self.size().toTuple()
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(247, 241, 231))  # 199,199,233
        painter.drawRect(0, h-self.box_h-20, w, self.box_h+20)

        painter.setBrush(QColor(249,245,238))  # 77,199,145
        painter.drawRect(0, h-self.box_h-70, w, 50)

    def resizeEvent(self, event):
        w, h = event.size().toTuple()
        # from buttom to top
        self.timelabel.setGeometry(10, h-self.box_h-20, self.timelabel_w,
                                   self.box_h+20)
        box_x, box_y = w-self.box_w-10, h-self.box_h-10
        self.box.move(box_x, box_y)
        self.tageditor.setGeometry(20, box_y-35, w-40, self.tageditor_h)
        self.editor.setGeometry(0, self.title_h, w, box_y-60)
        self.titleeditor.resize(w, self.title_h)

    def showEvent(self, event):
        self.editor.setFocus()
        self.editor.moveCursor(QTextCursor.Start)

    def updateTagEditorFont(self, text):
        "Set tageditor's placeHoderFont to italic"
        fontstyle = 'normal' if text else 'italic'
        self.tageditor.setStyleSheet('font-style: %s' % fontstyle)

    def startTimeEditor(self, event):
        if self.created is None: return  # new diary
        clicked, time = DateTimeDialog.getDateTime(self.created, self)
        if clicked and time!=self.created:
            self.created = time
            self.timeModified = True


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
    '''The widget used to edit diary contents in Editor window.

    setXX methods are used in NTextDocument(in NikkiList preview),
    first load of NTextEdit,NTextEdit's context-menu.
    '''
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

        self.creActs()
        self.setModified(False)

    def creActs(self):
        self.submenu = QMenu(self.tr('Format'))
        self.hlAct = QAction(QIcon(':/fmt/highlight.png'), self.tr('Highlight'),
                             self, shortcut=QKeySequence('Ctrl+H'))
        self.soAct = QAction(QIcon(':/fmt/strikeout.png'), self.tr('Strike out'),
                             self, shortcut=QKeySequence('Ctrl+-'))
        self.bdAct = QAction(QIcon(':/fmt/bold.png'), self.tr('Bold'),
                             self, shortcut=QKeySequence('Ctrl+B'))
        self.ulAct = QAction(QIcon(':/fmt/underline.png'), self.tr('Underline'),
                             self, shortcut=QKeySequence('Ctrl+U'))
        self.itaAct = QAction(QIcon(':/fmt/italic.png'), self.tr('Italic'),
                              self, shortcut=QKeySequence('Ctrl+I'))

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
        self.clrAct = QAction(self.tr('Clear format'), self,
                              shortcut=QKeySequence('Ctrl+D'))
        self.addAction(self.clrAct)
        self.submenu.addAction(self.clrAct)
        self.clrAct.triggered.connect(self.clearformat)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu(event.globalPos())
        before = menu.actions()[2]

        cur = self.textCursor()
        if cur.hasSelection():
            curtfmt = cur.charFormat()
            self.hlAct.setChecked(True if curtfmt.background().color() == \
                                  QColor(255, 250, 160) else False)
            self.bdAct.setChecked(True if curtfmt.fontWeight() == QFont.Bold \
                                  else False)
            self.soAct.setChecked(curtfmt.fontStrikeOut())
            self.ulAct.setChecked(curtfmt.fontUnderline())
            self.itaAct.setChecked(curtfmt.fontItalic())
            self.submenu.setEnabled(True)
        else:
            self.submenu.setEnabled(False)

        menu.insertSeparator(before)
        menu.insertMenu(before, self.submenu)
        menu.exec_(event.globalPos())

    def setHL(self, pre=False):
        fmt = self.textCursor().charFormat()
        if pre:  # called by NTextDocument
            hasFormat = False
        else:  # called by NTextEdit(Editor's context menu)
            hasFormat = (fmt.background().color() == QColor(255, 250, 160))

        fmt.setBackground(QBrush(Qt.white if hasFormat
                                 else QColor(255, 250, 160)))
        self.textCursor().mergeCharFormat(fmt)

    def setBD(self, pre=False):
        fmt = self.textCursor().charFormat()
        if pre:
            hasFormat = False
        else:
            hasFormat = (fmt.fontWeight() == QFont.Bold)

        fmt.setFontWeight(QFont.Normal if hasFormat else QFont.Bold)
        self.textCursor().mergeCharFormat(fmt)

    def setSO(self, pre=False):
        fmt = self.textCursor().charFormat()
        if pre:
            hasFormat = False
        else:
            hasFormat = fmt.fontStrikeOut()

        fmt.setFontStrikeOut(not hasFormat)
        self.textCursor().mergeCharFormat(fmt)

    def setUL(self, pre=False):
        fmt = self.textCursor().charFormat()
        if pre:
            hasFormat = False
        else:
            hasFormat = fmt.fontUnderline()

        fmt.setFontUnderline(not hasFormat)
        self.textCursor().mergeCharFormat(fmt)

    def setIta(self, pre=False):
        fmt = self.textCursor().charFormat()
        if pre:
            hasFormat = False
        else:
            hasFormat = fmt.fontItalic()

        fmt.setFontItalic(not hasFormat)
        self.textCursor().mergeCharFormat(fmt)

    def clearformat(self):
        fmt = QTextCharFormat()
        self.textCursor().setCharFormat(fmt)

    def keyPressEvent(self, event):
        "Auto-indent support"
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

    def insertFromMimeData(self, source):
        "Disable some unsuportted types"
        self.insertHtml(source.html() or source.text())


class NTextDocument(QTextDocument):
    '''Read format info from database and apply it.'''
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


class DateTimeDialog(QDialog):
    timeFmt = "yyyy/MM/dd HH:mm"
    def __init__(self, timestr, parent=None):
        super(DateTimeDialog, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr('Edit created time'))
        self.setMinimumWidth(100)

        self.verticalLayout = QVBoxLayout(self)

        dt = QDateTime.fromString(timestr, self.timeFmt)
        self.dtEdit = QDateTimeEdit(dt)
        self.dtEdit.setDisplayFormat(self.timeFmt)
        self.verticalLayout.addWidget(self.dtEdit)

        self.btnBox = QDialogButtonBox()
        self.btnBox.setOrientation(Qt.Horizontal)
        self.btnBox.setStandardButtons(QDialogButtonBox.Ok |
                                       QDialogButtonBox.Cancel)
        self.verticalLayout.addWidget(self.btnBox)

        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)

    @staticmethod
    def getDateTime(timestr, parent):
        "Run Dialog,return None if canceled,otherwise return timestr"
        dtDialog = DateTimeDialog(timestr, parent)
        # result code is 1 if OK clicked else 0
        code = dtDialog.exec_()
        return (code, dtDialog.dtEdit.dateTime().toString(dtDialog.timeFmt))


class Main(QWidget):
    def __init__(self):
        super(Main, self).__init__()
        self.restoreGeometry(settings.value("Main/windowGeo"))
        self.setWindowTitle('Hazama Prototype Ver'+str(__version__))

        self.nlist = NList()
        self.nlist.load()
        self.tlist = TList()
        self.splitter = MainSplitter()
        self.toolbar = QToolBar()
        self.searchbox = SearchBox()
        self.countlabel = QLabel()

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        # setuo MainSplitter
        self.splitter.splitterMoved.connect(self.keepTList)
        self.searchbox.textChanged.connect(self.filter)
        self.splitter.addWidget(self.tlist)
        self.splitter.addWidget(self.nlist)
        for i in range(2):
            self.splitter.setCollapsible(i, False)

        # setup ToolBar
        self.creActs()  #create actions
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setStyleSheet('QToolBar{background: rgb(242, 241, 231);'
                                   'border-bottom: 1px solid rgb(182, 189, 197);'
                                   'padding: 2px; spacing: 2px}')
        self.sorAct.setMenu(SortOrderMenu())
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
        if not int(settings.value('Main/TListVisible', 0)): self.tlist.hide()

    def closeEvent(self, event):
        settings.setValue('Main/windowGeo', self.saveGeometry())
        TListWidth = self.splitter.sizes()[0]
        if TListWidth == 0:
            settings.setValue('Main/TListVisible', 0)
        else:
            settings.setValue('Main/TListVisible', 1)

        event.accept()
        qApp.quit()

    def keepTList(self, pos=None, index=None, init=False):
        "keep TList's size when reducing window's width"
        if init:
            self.setMinimumWidth(int(settings.value('Main/TListWidth'))+350+2)
        else:
            if self.tlist.isVisible():
                self.setMinimumWidth(pos+350+2)

    def filter(self, text=None):
        "Connected to SearchBox and TList.text belongs to SearchBox's event"
        text = self.searchbox.text()
        try:
            tagid = self.tlist.currentItem().data(1)
        except AttributeError:  # TList hidden
            tagid = None
        search = text if text else None

        if tagid == 'All':
            self.nlist.clear()
            self.nlist.load(search=search)
        else:
            self.nlist.clear()
            self.nlist.load(tagid=tagid, search=search)

    def creActs(self):
        self.tlistAct = QAction(QIcon(':/images/tlist.png'), self.tr('Tag List'),
                                self, shortcut=QKeySequence('F5'))
        self.tlistAct.setCheckable(True)
        self.creAct = QAction(QIcon(':/images/new.png'), self.tr('New'), self)
        self.delAct = QAction(QIcon(':/images/delete.png'), self.tr('Delete'), self)
        self.sorAct = QAction(QIcon(':/images/sort.png'), self.tr('Sort By'), self)
        self.cfgAct = QAction(QIcon(':/images/config.png'), self.tr('Settings'), self)

        self.tlistAct.triggered[bool].connect(self.setTList)
        self.creAct.triggered.connect(self.nlist.newNikki)
        self.delAct.triggered.connect(self.nlist.delNikki)
        self.cfgAct.triggered.connect(self.startConfigDialog)

    def startConfigDialog(self):
        self.cfgdialog = ConfigDialog()
        self.cfgdialog.show()

    def setTList(self, checked):
        self.tlist.setVisible(checked)

    def showEvent(self, event):
        self.nlist.setFocus()

    def updateCountLabel(self):
        "Only called when diary saving or deleting"
        self.countlabel.setText(self.tr('%i diary') % nikki.count())


class SortOrderMenu(QMenu):
    '''Menu used to Change sort order of NList.'''
    def __init__(self):
        super(SortOrderMenu, self).__init__()
        self.aboutToShow.connect(self.setActs)

        self.bycreated = QAction(self.tr('Created Date'), self)
        self.bymodified = QAction(self.tr('Modified Date'), self)
        self.bytitle = QAction(self.tr('Title'), self)
        self.bylength = QAction(self.tr('Length'), self)
        self.reverse = QAction(self.tr('Reverse'), self)
        self.reverse.setCheckable(True)

        self.ordertypes = [self.bycreated, self.bymodified, self.bytitle, self.bylength]
        for a in self.ordertypes:
            a.setCheckable(True)
            self.addAction(a)
        self.addSeparator()
        self.addAction(self.reverse)

        self.bycreated.triggered[bool].connect(self.setCR)
        self.bymodified.triggered[bool].connect(self.setMD)
        self.bytitle.triggered[bool].connect(self.setTT)
        self.bylength.triggered[bool].connect(self.setLT)
        self.reverse.triggered[bool].connect(self.setRE)

    def setActs(self):
        "Set actions checked/unchecked before showing"
        order, reverse = main.nlist.getOrder()
        for a in self.ordertypes: a.setChecked(False)
        enabled = getattr(self, 'by'+order)
        enabled.setChecked(True)
        self.reverse.setChecked(reverse)

    def setCR(self, checked):
        if checked:
            settings.setValue('NList/sortOrder', 'created')
            main.nlist.clear()
            main.nlist.load()

    def setMD(self, checked):
        if checked:
            settings.setValue('NList/sortOrder', 'modified')
            main.nlist.clear()
            main.nlist.load()

    def setTT(self, checked):
        if checked:
            settings.setValue('NList/sortOrder', 'title')
            main.nlist.clear()
            main.nlist.load()

    def setLT(self, checked):
        if checked:
            settings.setValue('NList/sortOrder', 'length')
            main.nlist.clear()
            main.nlist.load()

    def setRE(self, checked):
        settings.setValue('NList/sortReverse', int(checked))
        main.nlist.clear()
        main.nlist.load()


class TList(QListWidget):
    def __init__(self):
        super(TList, self).__init__()
        self.setItemDelegate(TListDelegate())
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setUniformItemSizes(True)
        self.setStyleSheet(TListDelegate.TListSS)

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

    def showEvent(self, event):
        self.load()
        main.keepTList(init=True)
        self.setCurrentRow(0)
        # avoid refreshing nlist by unexpected signal
        self.itemSelectionChanged.connect(main.filter)
        main.tlistAct.setChecked(True)

    def hideEvent(self, event):
        # Reset minimumWidth which set by Main.keepTList
        main.setMinimumWidth(350)
        # currentItem is None when tag deleted
        if self.currentItem() is None or self.currentItem().data(1)!='All':
            self.setCurrentRow(0)
        # avoid refreshing nlist by unexpected signal
        self.itemSelectionChanged.disconnect(main.filter)
        settings.setValue('Main/TListWidth', main.splitter.sizes()[0])

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
        handle = TSplitterHandle(Qt.Horizontal, self)
        handle.setCursor(Qt.SizeHorCursor)
        return handle


class TSplitterHandle(QSplitterHandle):
    def paintEvent(self, event):
        w, h = self.size().toTuple()
        painter = QPainter(self)
        painter.fillRect(0, 0, w-1, h, QColor(234, 182, 138))  # same as bg of TList
        painter.fillRect(w-1, 0, 1, h, QColor(181, 61, 0))


class SearchBox(QLineEdit):
    def __init__(self, parent=None):
        super(SearchBox, self).__init__(parent)

        self.button = QToolButton(self)
        self.button.setFixedSize(18, 18)
        self.button.setCursor(Qt.ArrowCursor)
        self.button.clicked.connect(self.clear)

        self.textChanged.connect(self.update)
        self.setPlaceholderText(self.tr('Search'))
        self.update('')

    def resizeEvent(self, event):
        w, h = event.size().toTuple()
        pos_y = (h-18) / 2
        self.button.move(w-16-pos_y, pos_y)

    def update(self, text):
        iconame = 'search_clr' if text else 'search'
        fontstyle = 'normal' if text else 'italic'
        self.button.setStyleSheet('QToolButton{border: none;'
                                  'background: url(:/images/%s.png);'
                                  'background-position: center}' % iconame)
        self.setStyleSheet('QLineEdit{font-style: %s}' % fontstyle)


class ConfigDialog(QDialog, ui.configdialog.Ui_Settings):
    # first try that using Qt Designer generated UI.
    lang2index = {'en': 0, 'zh_CN': 1, 'ja': 2}  # index used in combo
    index2lang = {b: a for (a, b) in lang2index.items()}
    def __init__(self):
        super(ConfigDialog, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.setFont(sysfont)

        self.locEdit.setText(dbPath)
        self.aindCheck.setChecked(int(settings.value('Editor/autoindent', 1)))
        self.copenCheck.setChecked(int(settings.value('Editor/centeropen', 0)))
        self.langCombo.setCurrentIndex(self.lang2index[
                                       settings.value('Main/lang', 'en')])

    def closeEvent(self, event):
        del main.cfgdialog
        event.accept()

    def accept(self):
        settings.setValue('Editor/autoindent', int(self.aindCheck.isChecked()))
        settings.setValue('Editor/centeropen', int(self.copenCheck.isChecked()))
        lang = self.index2lang[self.langCombo.currentIndex()]
        if settings.value('Main/lang') != lang:
            settings.setValue('Main/lang', lang)
            set_trans(settings)
            restart_main()

        logging.info('Settings saved')
        super(ConfigDialog, self).accept()

    @Slot()
    def on_exportBtn_clicked(self):
        export_all = not bool(self._ui.exportOption.currentIndex())
        file, t = QFileDialog.getSaveFileName(parent=self, filter=self.filter_s)
        export_xml = True if 'xml' in t else False
        if export_xml:
            if export_all:
                nikki.exportXml(file)
            else:
                for i in main.nlist.selectedItems(): print(i.data(2)['id'])



if __name__ == '__main__':
    timee = time.clock()
    app = QApplication(sys.argv)
    settings = QSettings(path+'config.ini', QSettings.IniFormat)

    set_trans(settings)

    # setup fonts
    titlefont = NFont(s=settings.value('/Font/title'))
    tfontm = QFontMetrics(titlefont)
    datefont = NFont(s=settings.value('/Font/datetime'))
    dfontm = QFontMetrics(datefont)
    textfont = NFont(s=settings.value('/Font/text'))  # WenQuanYi Micro Hei
    txfontm = QFontMetrics(textfont)

    sysfont = app.font()
    defaultfont = NFont('Microsoft YaHei')
    defaultfont.setPointSize(app.font().pointSize())
    defontm = QFontMetrics(defaultfont)
    app.setFont(defaultfont)



    try:
        socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.bind(('127.0.0.1', 5002))
    except OSError:
        logging.warning('already running,exit')
        msgbox = QMessageBox()
        msgbox.setText(qApp.translate('FailStart',
                                      'Hazama is already running'))
        msgbox.setWindowTitle('Hazama')
        msgbox.exec_()
        sys.exit()

    logging.basicConfig(level=logging.DEBUG)
    dbPath = settings.value('/Main/dbPath', 'nikkichou.db')
    nikki = Nikki(dbPath if os.sep in dbPath else path+dbPath)
    logging.info(str(nikki))

    main = Main()
    main.show()
    logging.debug('startup take %s seconds' % round(time.clock()-timee,3))
    sys.exit(app.exec_())
