from PySide.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide.QtGui import qApp
from hazama.config import db, settings


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
            # e.g. len(nikki)==10: [10]; len(nikki)==450: [35, 300, 80]
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
            for count in range(times):
                i = next(iterator)
                self._lst.append([i['id'], i['datetime'], i['text'], i['title'],
                                  i['tags'], i['formats']])
                if count & 15 == 0: qApp.processEvents()  # equals "row % 16 == 0"
            self.endInsertRows()

    def getRowById(self, id_):
        # user tends to modify newer diaries?
        for idx, d in enumerate(reversed(self._lst)):
            if d[0] == id_:
                return len(self._lst) - 1 - idx
        raise KeyError

    def getNikkiDictByRow(self, row):
        r = self._lst[row]
        return dict(id=r[0], title=r[3], datetime=r[1], text=r[2],
                    tags=r[4], formats=r[5])

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
            self._lst.insert(i, [None, '', '', '', '', None])
        self.endInsertRows()
        return True

    def insertRow(self, row, *__):
        return self.insertRows(row, 1)

    def updateDiary(self, diary):
        realId = db.save(**diary)
        # write to model
        oneRow = ([realId] +
                  [diary[k] for k in ('datetime', 'text', 'title', 'tags', 'formats')])
        if diary['id'] == -1:  # new diary
            row = self.rowCount()
            self.insertRow(row)
            # tags may be None while tags is empty or not changed
            if oneRow[4] is None: oneRow[4] = ''
        else:
            row = self.getRowById(diary['id'])
            if oneRow[4] is None: oneRow[4] = self._lst[row][4]
        self._lst[row] = oneRow
        self.dataChanged.emit(self.index(row, 0), self.index(row, 6))
        return row
