import logging
from PySide.QtGui import *
from PySide.QtCore import *
from hazama.ui import font, refreshStyle
from hazama.ui.customobjects import DragScrollMixin
from hazama.ui.customwidgets import NElideLabel
from hazama.config import settings, db


class TagListDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.h = font.default_m.height() + 8

    def paint(self, painter, option, index):
        x, y, w = option.rect.x(), option.rect.y(), option.rect.width()
        tag, count = index.data(Qt.DisplayRole), index.data(Qt.UserRole)
        if count is not None:
            count = str(count)
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
            tag = font.default_m.elidedText(
                tag, Qt.ElideRight,
                w-12 if count is None else w-font.datetime_m.width(count)-12)
            painter.drawText(textArea, Qt.AlignVCenter | Qt.AlignLeft, tag)
            # draw tag count
            if count is not None:
                painter.setFont(font.datetime)
                painter.drawText(textArea, Qt.AlignVCenter | Qt.AlignRight, count)

    def createEditor(self, parent, option, index):
        # delegate will hold the reference to editor
        editor = QLineEdit(parent, objectName='tagListEdit')
        editor.oldText = index.data()
        return editor

    def updateEditorGeometry(self, editor, option, index):
        rect = option.rect
        rect.translate(1, 1)
        rect.setWidth(rect.width() - 2)
        rect.setHeight(rect.height() - 1)
        editor.setGeometry(rect)

    def sizeHint(self, option, index):
        return QSize(-1, self.h)


class TagListDelegateColorful(QItemDelegate):
    """ItemDelegate of theme 'colorful' for TagList. Using widget rendering."""
    class ItemWidget(QFrame):
        # almost the same as DiaryListDelegateColorful.ItemWidget
        def __init__(self, parent=None):
            super().__init__(parent, objectName='TagListItem')
            self._hLayout = QHBoxLayout(self)
            self._hLayout.setContentsMargins(0, 0, 0, 0)

            self.name = NElideLabel(self, objectName='TagListItemName')
            self.name.setAlignment(Qt.AlignRight)
            self.name.elideMode = Qt.ElideLeft
            self.count = QLabel(self, objectName='TagListItemCount')
            self.count.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
            self._hLayout.addWidget(self.count)
            self._hLayout.addWidget(self.name)

        def setFixedWidth(self, w):
            if w != self.width():
                super().setFixedWidth(w)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._itemW = self.ItemWidget()
        self._itemW.setFixedHeight(self._itemW.sizeHint().height())
        self._countEnabled = settings['Main'].getboolean('tagListCount')
        if not self._countEnabled: self._itemW.count.hide()

    def paint(self, painter, option, index):
        selected = bool(option.state & QStyle.State_Selected)
        active = bool(option.state & QStyle.State_Active)

        self._itemW.name.setText(index.data(Qt.DisplayRole))
        if self._countEnabled:
            countData = index.data(Qt.UserRole)
            self._itemW.count.setText(str(countData) if countData else '')
        self._itemW.setProperty('selected', selected)
        self._itemW.setProperty('active', active)
        refreshStyle(self._itemW)
        self._itemW.setFixedWidth(option.rect.width())

        painter.translate(option.rect.topLeft())
        self._itemW.render(painter, QPoint())
        painter.resetTransform()

    def sizeHint(self, option, index):
        return QSize(-1, self._itemW.height())

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent, objectName='tagListEdit')
        editor.setAlignment(self._itemW.name.alignment())
        editor.oldText = index.data()
        return editor

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class TagList(DragScrollMixin, QListWidget):
    currentTagChanged = Signal(str)  # str is tag-name or ''
    tagNameModified = Signal(str)  # arg: newTagName

    def __init__(self, parent=None):
        DragScrollMixin.__init__(self)
        QListWidget.__init__(self, parent)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setupTheme()

        self.setUniformItemSizes(True)
        self.currentItemChanged.connect(self.onCurrentItemChanged)
        nextFunc = lambda: self.setCurrentRow(
            0 if self.currentRow() == self.count() - 1 else self.currentRow() + 1)
        preFunc = lambda: self.setCurrentRow((self.currentRow() or self.count()) - 1)
        self.nextSc = QShortcut(QKeySequence('Ctrl+Tab'), self, activated=nextFunc)
        self.preSc = QShortcut(QKeySequence('Ctrl+Shift+Tab'), self, activated=preFunc)

    def contextMenuEvent(self, event):
        # ignore "All" item. cursor must over the item
        index = self.indexAt(event.pos())
        if index.row() > 0:
            menu = QMenu()
            menu.addAction(QAction(self.tr('Rename'), menu,
                                   triggered=lambda: self.edit(index)))
            menu.exec_(event.globalPos())
            menu.deleteLater()

    def commitData(self, editor):
        newName = editor.text()
        if editor.isModified() and newName and ' ' not in newName:
            # editor.oldText is set in delegate
            db.change_tag_name(editor.oldText, newName)
            logging.info('tag [%s] changed to [%s]', editor.oldText, newName)
            super().commitData(editor)
            self.tagNameModified.emit(newName)

    def load(self):
        logging.debug('load Tag List')
        QListWidgetItem(self.tr('All'), self)
        self.setCurrentRow(0)
        itemFlag = Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if settings['Main'].getboolean('tagListCount'):
            for name, count in db.get_tags(count=True):
                item = QListWidgetItem(name, self)
                item.setFlags(itemFlag)
                item.setData(Qt.ToolTipRole, name)
                item.setData(Qt.UserRole, count)
        else:
            for name in db.get_tags(count=False):
                item = QListWidgetItem(name, self)
                item.setData(Qt.ToolTipRole, name)
                item.setFlags(itemFlag)

    def reload(self):
        if not self.isVisible():
            return

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

    def setupTheme(self):
        theme = settings['Main']['theme']
        d = {'colorful': TagListDelegateColorful}.get(theme, TagListDelegate)
        self.setItemDelegate(d())  # do not pass parent under PySide...
        # force items to be laid again
        self.setSpacing(self.spacing())

    def onCurrentItemChanged(self, currentItem):
        tag = currentItem.data(Qt.DisplayRole) if currentItem else ''
        # tag is '' if no selection
        self.currentTagChanged.emit('' if currentItem is self.item(0) else tag)
