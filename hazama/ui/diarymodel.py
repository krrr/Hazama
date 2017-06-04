import time
import logging
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
    ROW_WIDTH = 7
    ID, DATETIME, TEXT, TITLE, TAGS, FORMATS, LENGTH = range(ROW_WIDTH)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lst = []
        self._yearFirstsArgs = None
        self._yearFirsts = None

    def rowCount(self, parent=None):
        return len(self._lst)

    def columnCount(self, parent=None):
        return DiaryModel.ROW_WIDTH

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return
        d, col = self._lst[index.row()], index.column()
        if col == DiaryModel.LENGTH:
            return len(d[DiaryModel.TEXT])
        else:
            return d[col]

    def setData(self, index, value, role=Qt.DisplayRole):
        self._lst[index.row()][index.column()] = value
        self.dataChanged.emit(index, index)
        return True

    def removeRows(self, row, count, parent=None):
        self.beginRemoveRows(QModelIndex(), row, row+count-1)
        del self._lst[row:row+count]
        self.endRemoveRows()
        return True

    def insertRows(self, row, count, parent=None):
        self.beginInsertRows(QModelIndex(), row, row+count-1)
        for i in range(row, row+count):
            self._lst.insert(i, list(db.EMPTY_DIARY))
        self.endInsertRows()
        return True

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
        self.dataChanged.emit(self.index(row, 0), self.index(row, DiaryModel.ROW_WIDTH-1))
        return row

    def loadFromDb(self):
        """Load diaries from database. It will repeatedly call qApp.processEvents
        while loading data, making UI still responsive if the amount of data
        is big. It also delay informing views to update, this avoid unnecessary
        layout operation."""
        start_time = time.clock()
        sortBy = settings['Main']['listSortBy']
        reverse = settings['Main'].getboolean('listReverse')
        self._yearFirstsArgs = (sortBy, reverse)
        iterator = db.sorted(sortBy, reverse)

        firstChunk = True
        rest = len(db)
        yearFirsts = {}
        yearBefore = None
        while rest > 0:  # process COUNT items and inform the view in every iteration
            if firstChunk:
                firstChunk = False
                count = min(35, rest)
            else:
                count = min(300, rest)

            nextRow = len(self._lst)
            self.beginInsertRows(QModelIndex(), nextRow, nextRow+count-1)
            for i in range(count):
                d = list(next(iterator))

                # save year firsts
                year = d[1][:4]
                if year != yearBefore and nextRow+i > 0:
                    yearFirsts[int(yearBefore)] = nextRow+i-1 if reverse else nextRow+i
                yearBefore = year
                # end saving year firsts

                self._lst.append(d)
                if i % 15 == 0:
                    qApp.processEvents()
            self.endInsertRows()
            rest -= count  # count may become minus

        pairs = yearFirsts.items() if sortBy == 'datetime' else ()
        self._yearFirsts = tuple(sorted(pairs, reverse=reverse))
        logging.debug('loadFromDb took %.2f sec', time.clock()-start_time)

    def getYearFirsts(self):
        """Get (year: row) pairs. row is the row of the first diary of each year (excluding
        the year at last of the diary list). This is calculated in loadFromDb."""
        # access model using QModelIndex is slow, and user rarely changes
        # sortBy, so calculate it once when loading
        sortBy = settings['Main']['listSortBy']
        reverse = settings['Main'].getboolean('listReverse')
        return self._yearFirsts if (sortBy, reverse) == self._yearFirstsArgs else ()

    def getRowById(self, id_):
        # user tends to modify newer diaries?
        for idx, d in enumerate(reversed(self._lst)):
            if d[DiaryModel.ID] == id_:
                return len(self._lst) - 1 - idx
        raise KeyError

    def getDiaryDictByRow(self, row):
        return diary2dict(self._lst[row])

    def clear(self):
        self.beginRemoveRows(QModelIndex(), 0, self.rowCount())
        self._lst.clear()
        self.endRemoveRows()

    def getAll(self):
        # using data() is slow, because it will create many index objects
        for i in self._lst:
            yield tuple(i) + (len(i[DiaryModel.TEXT]),)
