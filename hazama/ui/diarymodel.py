from PySide.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide.QtGui import qApp
from hazama.config import db, settings
from hazama.diarybook import diary2dict, dict2diary


class DiaryModel(QAbstractTableModel):
    """In memory copy of diary database. Specially optimized for loading from database.
    All attempts to reduce memory usage were failed, because setLayoutMode didn't work,
    and the view will still issue a huge amount of queries.
    Table structure: id | datetime | text | title | tags | formats | len(text)
    """
    ID, DATETIME, TEXT, TITLE, TAGS, FORMATS, LENGTH = range(7)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lst = []

    def loadFromDb(self):
        """Load diaries from database. It will repeatedly call qApp.processEvents
        while loading data, making UI still responsive if the amount of data
        is big. It also delay informing views to update, this avoid unnecessary
        layout operation."""
        def makeTimesSeq():
            # e.g. len(db)==10: [10]; len(db)==450: [35, 300, 80]
            # let first chunk be smallest to decreasing the time of blank-list
            chunkSz, firstChunkSz = 300, 35
            l = len(db)
            if l <= firstChunkSz:
                return [l]

            rest = l - firstChunkSz
            seq = [firstChunkSz] + [chunkSz] * (rest // chunkSz)
            return seq + [rest % chunkSz] if rest % chunkSz != 0 else seq

        iterator = db.sorted(settings['Main']['listSortBy'],
                             settings['Main'].getboolean('listReverse'))
        for times in makeTimesSeq():
            # informing view every TIMES iterations
            nextRow = len(self._lst)
            self.beginInsertRows(QModelIndex(), nextRow, nextRow+times-1)
            for i in range(times):
                self._lst.append(list(next(iterator)))
                if i & 15 == 0: qApp.processEvents()  # equals "row % 16 == 0"
            self.endInsertRows()

    def getRowById(self, id_):
        # user tends to modify newer diaries?
        for idx, d in enumerate(reversed(self._lst)):
            if d[0] == id_:
                return len(self._lst) - 1 - idx
        raise KeyError

    def getDiaryDictByRow(self, row):
        return diary2dict(self._lst[row])

    def clear(self):
        self.removeRows(0, self.rowCount())

    def rowCount(self, *__):
        return len(self._lst)

    def columnCount(self, *__):
        return 7

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return
        d, col = self._lst[index.row()], index.column()
        if col == 6:  # len(text)
            return len(d[2])
        else:
            return d[col]

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

    def removeRow(self, row, *__):
        return self.removeRows(row, 1)

    def insertRows(self, row, count, *__):
        self.beginInsertRows(QModelIndex(), row, row+count-1)
        for i in range(row, row+count):
            self._lst.insert(i, list(db.EMPTY_DIARY))
        self.endInsertRows()
        return True

    def insertRow(self, row, *__):
        return self.insertRows(row, 1)

    def saveDiary(self, dic):
        assert isinstance(dic, dict)
        realId = db.save(dic)
        # write to model
        diary = dict2diary(dic, as_list=True)
        if diary[self.ID] == -1:  # new diary
            row = self.rowCount()
            self.insertRow(row)
            diary[self.ID] = realId
        else:
            row = self.getRowById(diary[self.ID])
            if diary[self.TAGS] is None:  # tags not changed
                diary[self.TAGS] = self._lst[row][self.TAGS]
        self._lst[row] = diary
        self.dataChanged.emit(self.index(row, 0), self.index(row, 6))
        return row
