from PySide.QtCore import *
from PySide.QtGui import *
from hazama.config import nikki, settings


class NikkiModel(QAbstractTableModel):
    """The Model holds diaries. Specially optimized for loading from database."""
    def __init__(self, parent=None):
        super(NikkiModel, self).__init__(parent)
        self._lst = []

    def loadFromDb(self):
        """Load diaries from database. It will repeatedly call qApp.processEvents
        while loading data, making UI remaining responsive if the amount of data
        is big. It also delay informing views to update, this avoid unnecessary
        layout operation."""
        def makeTimesSeq():
            """e.g. len(nikki)==10: [10]; len(nikki)==450: [70, 300, 80]"""
            # let first chunk be smallest to decreasing the time of blank-list
            chunkSz, firstChunkSz = 300, 35
            l = len(nikki)
            if l < firstChunkSz:
                return [l]
            else:
                restChunkSz = l - firstChunkSz
                return ([firstChunkSz] + [chunkSz] * (restChunkSz // chunkSz) +
                        [restChunkSz % chunkSz])

        sortBy = settings['Main'].get('listSortBy', 'datetime')
        reverse = settings['Main'].getboolean('listReverse', True)

        iterator = nikki.sorted(sortBy, reverse)
        for times in makeTimesSeq():
            # informing view every TIMES iterations
            nextRow = len(self._lst)
            self.beginInsertRows(QModelIndex(), nextRow, nextRow+times-1)
            for count in range(times):
                i = next(iterator)
                self._lst.append([i['id'], i['datetime'], i['text'], i['title'],
                                  i['tags'], i['formats'], len(i['text'])])
                if count & 15 == 0: qApp.processEvents()  # equals "row % 16 == 0"
            self.endInsertRows()

    def getRowById(self, id):
        for row, i in enumerate(self._lst):
            if i[0] == id: return row
        return -1

    def clear(self): self.removeRows(0, self.rowCount())

    def rowCount(self, *__): return len(self._lst)

    def columnCount(self, *__): return 7

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self._lst[index.row()][index.column()]

    def setData(self, index, value, *__):
        r, c = index.row(), index.column()
        self._lst[r][c] = value
        self.dataChanged.emit(*[self.index(r, c)] * 2)
        return True

    def removeRows(self, row, count, *__):
        self.beginRemoveRows(QModelIndex(), row, row+count-1)
        del self._lst[row:row+count]
        self.endRemoveRows()
        return True

    def removeRow(self, row, *__): return self.removeRows(row, 1)

    def insertRows(self, row, count, *__):
        self.beginInsertRows(QModelIndex(), row, row+count-1)
        for i in range(row, row+count):
            self._lst.insert(i, [None] * 7)
        self.endInsertRows()
        return True

    def insertRow(self, row, *__): return self.insertRows(row, 1)

    def updateNikki(self, nikkiDict):
        realId = nikki.save(**nikkiDict)
        # write to model
        oneRow = ([realId] +
                  list(map(lambda k: nikkiDict[k],
                           ['datetime', 'text', 'title', 'tags', 'formats'])) +
                  [len(nikkiDict['text'])])
        if nikkiDict['id'] == -1:  # new diary
            row = self.rowCount()
            self.insertRow(row)
            # tags may be None while tags is empty or not changed
            if oneRow[4] is None: oneRow[4] = ''
        else:
            row = self.getRowById(nikkiDict['id'])
            if oneRow[4] is None: oneRow[4] = self._lst[row][4]
        self._lst[row] = oneRow
        self.dataChanged.emit(self.index(row, 0), self.index(row, 6))
        return row
