from PySide.QtGui import *
from PySide.QtCore import *
from itertools import chain
from hazama.ui import getDpiScaleRatio

# the default colors that represent heat of data, from cold to hot
defCellColors = (QColor(255, 255, 255), QColor(255, 243, 208),
                 QColor(255, 221, 117), QColor(255, 202, 40))


class HeatMap(QWidget):
    def __init__(self, *args, **kwargs):
        super(HeatMap, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.bar = QFrame(self, objectName='heatMapBar')
        barLayout = QHBoxLayout(self.bar)
        barLayout.setContentsMargins(0, 0, 0, 0)
        barLayout.setSpacing(3)
        # setup buttons and menu
        self.view = HeatMapView(self, font=self.font(), objectName='heatMapView')
        self.yearBtn = QPushButton(str(self.view.year), self,
                                   objectName='heatMapBtn')
        self.yearBtn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.yearBtn.setFocusPolicy(Qt.TabFocus)
        self.yearBtn.setFont(self.font())
        self.yearBtn.clicked.connect(self.yearBtnAct)
        self.yearMenu = QMenu(self, objectName='heatMapMenu')
        self._yearActGroup = QActionGroup(self.yearMenu)
        self.setupYearMenu()
        sz = QSize(16, 16) * getDpiScaleRatio()
        ico = QIcon(':/heatmap/arrow-left.png')
        ico.addFile(':/heatmap/arrow-left-big.png')
        preBtn = QToolButton(self, icon=ico, clicked=self.yearPre, iconSize=sz)
        ico = QIcon(':/heatmap/arrow-right.png')
        ico.addFile(':/heatmap/arrow-right-big.png')
        nextBtn = QToolButton(self, icon=ico, clicked=self.yearNext, iconSize=sz)
        # setup color sample
        self.sample = ColorSampleView(self, cellLen=11)
        # always bigger than sizeHint even policy is Maximum, so painful. use fixed
        self.sample.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.sample.setFixedSize(preBtn.sizeHint().width()*2 + barLayout.spacing(), 12)
        barLayout.addWidget(preBtn, Qt.AlignVCenter)
        barLayout.addWidget(nextBtn, Qt.AlignVCenter)
        barLayout.addSpacerItem(QSpacerItem(30, 1, QSizePolicy.Expanding, QSizePolicy.Fixed))
        barLayout.addWidget(self.yearBtn)
        barLayout.addSpacerItem(QSpacerItem(30, 1, QSizePolicy.Expanding, QSizePolicy.Fixed))
        barLayout.addWidget(self.sample)
        layout.addWidget(self.bar)
        layout.addWidget(self.view)
        # setup shortcuts
        self.preSc = QShortcut(QKeySequence(Qt.Key_Left), self, self.yearPre)
        self.nextSc = QShortcut(QKeySequence(Qt.Key_Right), self, self.yearNext)
        self.pre5Sc = QShortcut(QKeySequence(Qt.Key_Up), self, self.yearPre5)
        self.next5Sc = QShortcut(QKeySequence(Qt.Key_Down), self, self.yearNext5)

    def setupYearMenu(self):
        group, menu, curtYear = self._yearActGroup, self.yearMenu, self.view.year
        menu.clear()
        for y in chain([curtYear-10, curtYear-7], range(curtYear-4, curtYear)):
            menu.addAction(QAction(str(y), group, triggered=self.yearMenuAct))
        curtYearAc = QAction(str(curtYear), group)
        curtYearAc.setDisabled(True)
        curtYearAc.setCheckable(True)
        curtYearAc.setChecked(True)
        menu.addAction(curtYearAc)
        for y in chain(range(curtYear+1, curtYear+5), [curtYear+7, curtYear+10]):
            menu.addAction(QAction(str(y), group, triggered=self.yearMenuAct))

    def setColorFunc(self, f):
        """Set function that determine each cell's background color.
        This function will be called with args: year, month, day, cellColors.
        cellColors is something like defCellColors."""
        self.view.cellColorFunc = f

    def _moveYear(self, offset):
        self.view.year += offset
        self.yearBtn.setText(str(self.view.year))
        self.setupYearMenu()

    def yearPre(self): self._moveYear(-1)

    def yearNext(self): self._moveYear(1)

    def yearPre5(self): self._moveYear(-5)

    def yearNext5(self): self._moveYear(5)

    def yearMenuAct(self):
        yearStr = self.sender().text()
        self.view.year = int(yearStr)
        self.yearBtn.setText(yearStr)
        self.setupYearMenu()

    def yearBtnAct(self):
        """Popup menu manually to avoid indicator in YearButton"""
        self.yearMenu.exec_(self.yearBtn.mapToGlobal(
            QPoint(0, self.yearBtn.height())))

    def showEvent(self, event):
        # must call setupMap after style polished
        self.view.setupMap()
        cs = tuple(getattr(self.view, 'cellColor%d' % i) for i in range(4))
        self.sample.setColors(cs)
        self.sample.setupMap()
        event.accept()


class HeatMapView(QGraphicsView):
    cellColorFunc = lambda *args: Qt.white  # dummy
    cellLen = 9
    cellSpacing = 2
    monthSpacingX = 14
    monthSpacingY = 20
    nameFontPx = 9  # month name

    def __init__(self, *args, **kwargs):
        super(HeatMapView, self).__init__(*args, **kwargs)
        self.yearVal = QDate.currentDate().year()
        self.cellBorderColorVal = Qt.lightGray
        for idx, c in enumerate(defCellColors):
            setattr(self, '_cellColor%d' % idx, c)

        self.scene = QGraphicsScene(self)
        f = self.font()
        f.setPixelSize(self.nameFontPx)
        self.nameH = QFontMetrics(f).height()
        self.setFont(f)
        # short names, for convenience
        self._cd = cellDis = self.cellLen + self.cellSpacing
        self._mdx = monthDisX = cellDis * 6 + self.cellLen + self.monthSpacingX
        self._mdy = monthDisY = cellDis * 4 + self.cellLen + self.monthSpacingY
        self.scene.setSceneRect(0, 0, monthDisX*3-self.monthSpacingX,
                                monthDisY*4-self.monthSpacingY+self.nameH)
        self.setScene(self.scene)

    def setupMap(self):
        locale, date, font, nameH = QLocale(), QDate(), self.font(), self.nameH
        cellDis, monthDisX, monthDisY = self._cd, self._mdx, self._mdy
        cellColors = tuple(getattr(self, 'cellColor%d' % i) for i in range(4))
        for m in range(12):
            date.setDate(self.year, m+1, 1)
            # cells. 7 days per row, index of row: (d//7)
            monthItems = [QGraphicsRectItem(cellDis*d-(d//7)*cellDis*7, cellDis*(d//7),
                                            self.cellLen, self.cellLen)
                          for d in range(date.daysInMonth())]
            for (d, item) in enumerate(monthItems, 1):
                date.setDate(self.year, m+1, d)
                if date <= QDate.currentDate():
                    item.setPen(QPen(self.cellBorderColor))
                    item.setBrush(self.cellColorFunc(self.year, m+1, d, cellColors))
                else:
                    p = QPen(Qt.gray)
                    p.setStyle(Qt.DotLine)
                    item.setPen(p)
            monthGroup = self.scene.createItemGroup(monthItems)
            # 3 months per line
            x, y = monthDisX*m-(m//3)*monthDisX*3, monthDisY*(m//3)
            monthGroup.setPos(x, y+nameH)
            # month name
            monthText = self.scene.addSimpleText(locale.toString(date, 'MMM'), font)
            monthText.setPen(self.palette().color(QPalette.WindowText))
            nameW = monthText.boundingRect().width()
            monthText.setPos(x+(monthDisX-self.monthSpacingX-nameW)/2, y)

    def resizeEvent(self, event):
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def setCellBorderColor(self, color):
        self.cellBorderColorVal = color

    def getCellBorderColor(self):
        return self.cellBorderColorVal

    def getYear(self):
        return self.yearVal

    def setYear(self, year):
        self.yearVal = year
        self.scene.clear()
        self.setupMap()

    def getCellColor0(self): return self._cellColor0

    def setCellColor0(self, c): self._cellColor0 = c

    def getCellColor1(self): return self._cellColor1

    def setCellColor1(self, c): self._cellColor1 = c

    def getCellColor2(self): return self._cellColor2

    def setCellColor2(self, c): self._cellColor2 = c

    def getCellColor3(self): return self._cellColor3

    def setCellColor3(self, c): self._cellColor3 = c

    year = property(getYear, setYear)
    cellBorderColor = Property(QColor, getCellBorderColor, setCellBorderColor)
    cellColor0 = Property(QColor, getCellColor0, setCellColor0)
    cellColor1 = Property(QColor, getCellColor1, setCellColor1)
    cellColor2 = Property(QColor, getCellColor2, setCellColor2)
    cellColor3 = Property(QColor, getCellColor3, setCellColor3)


class ColorSampleView(QGraphicsView):
    def __init__(self, parent=None, cellLen=None):
        super(ColorSampleView, self).__init__(parent, objectName='heatMapSample',
                                              alignment=Qt.AlignRight)
        self._colors = defCellColors
        self.cellLen = cellLen if cellLen else 9
        self._descriptions = ('',) * 4

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.cellLen*len(self._colors), self.cellLen)
        self.setScene(self.scene)

    def setupMap(self):
        for index, c in enumerate(self._colors):
            item = QGraphicsRectItem(self.cellLen*index, 0, self.cellLen, self.cellLen)
            item.setToolTip(self._descriptions[index])
            item.setPen(QPen(Qt.darkGray))
            item.setBrush(c)
            self.scene.addItem(item)

    def setColors(self, colors):
        """Set colors to display, arg colors is a list of QColor"""
        self._colors = colors

    def setDescriptions(self, seq):
        if len(seq) != len(self._colors):
            raise Exception("The amount of description doesn't match color's")
        self._descriptions = tuple(seq)


if __name__ == '__main__':
    app = QApplication([])
    v = HeatMap()
    v.resize(500, 600)
    v.show()
    app.exec_()
