#include "heatmap.h"
#include "globals.h"
#include <QGraphicsScene>
#include <QShortcut>
#include <QMenu>
#include <QDate>
#include <QBoxLayout>
#include <QToolButton>
#include <QPushButton>
#include <QGraphicsRectItem>

const QVector<QColor> defCellColors = { QColor(255, 255, 255), QColor(255, 243, 208),
        QColor(255, 221, 117), QColor(255, 202, 40) };


HeatMapView::HeatMapView(QWidget *parent) : QGraphicsView(parent) {
    year = QDate::currentDate().year();
    cellColor0 = defCellColors[0];
    cellColor1 = defCellColors[1];
    cellColor2 = defCellColors[2];
    cellColor3 = defCellColors[3];

    cellColorFunc = [](int, const QList<QColor> &) { return Qt::white; };
    cellDataFunc = [](QDate) { return 0; };

    auto scene = new QGraphicsScene(this);
    // short names, for convenience
    cellDis = cellLen + cellSpacing;
    monthDisX = cellDis * 6 + cellLen + monthSpacingX;
    monthDisY = cellDis * 4 + cellLen + monthSpacingY;
    setScene(scene);
}

void HeatMapView::resizeEvent(QResizeEvent *e) {
    Q_UNUSED(e);
    fitInView(scene()->sceneRect(), Qt::KeepAspectRatio);
}

void HeatMapView::setupMap() {
    auto nameFont = font();
    nameFont.setPixelSize(nameFontPx);
    int nameH = QFontMetrics(nameFont).height();
    scene()->setSceneRect(0, 0, monthDisX*3-monthSpacingX, monthDisY*4-monthSpacingY+nameH);

    auto locale = QLocale();
    auto date = QDate();
    auto curtDate = QDate::currentDate();
    auto cellColors = getCellColors();
    QPen cellPen(cellBorderColor);
    cellPen.setWidth((scaleRatio <= 1.5) ? 1 : 2);
    cellPen.setCosmetic(true);
    QPen emptyCellPen(cellPen);
    emptyCellPen.setStyle(Qt::DotLine);
    emptyCellPen.setColor(Qt::gray);

    for (int m : range(12)) {
        date.setDate(year, m+1, 1);
        // cells. 7 days per row, index of row: (day/7)
        QList<QGraphicsItem*> monthItems;
        for (int day : range(1, date.daysInMonth()+1)) {
            auto item = new QGraphicsRectItem(cellDis*day-(day/7)*cellDis*7, cellDis*(day/7),
                                              cellLen, cellLen);
            date.setDate(date.year(), date.month(), day);
            if (date <= curtDate) {
                item->setPen(cellPen);
                int data = cellDataFunc(date);
                if (data > 0) {
                    item->setBrush(cellColorFunc(data, cellColors));
                    item->setToolTip(QString("%1  (%2)").arg(data).arg(locale.toString(date)));
                }
            } else {
                item->setPen(emptyCellPen);
            }
            monthItems.append(item);
        }
        auto monthGroup = scene()->createItemGroup(monthItems);
        // 3 months per line
        int x = monthDisX*m-(m/3)*monthDisX*3, y = monthDisY*(m/3);
        monthGroup->setPos(x, y+nameH);
        // month name
        auto monthText = scene()->addSimpleText(locale.toString(date, "MMM"), nameFont);
        monthText->setBrush(palette().color(QPalette::WindowText));
        auto nameW = monthText->boundingRect().width();
        monthText->setPos(x+(monthDisX-monthSpacingX-nameW)/2, y);
    }
    fitInView(scene()->sceneRect(), Qt::KeepAspectRatio);
}

void HeatMapView::setYear(int y) {
    year = y;
    scene()->clear();
    setupMap();
}


HeatMap::HeatMap(QWidget *parent) : QWidget(parent) {
    setWindowFlags(Qt::Window | Qt::WindowCloseButtonHint);
    setAttribute(Qt::WA_DeleteOnClose);
    setWindowTitle(tr("Heat Map"));

    auto layout = new QVBoxLayout(this);
    layout->setSpacing(0);
    layout->setContentsMargins(0, 0, 0, 0);
    auto bar = new QFrame(this);
    bar->setObjectName("heatMapBar");
    auto barLayout = new QHBoxLayout(bar);
    barLayout->setContentsMargins(0, 0, scaleRatio, 0);
    barLayout->setSpacing(3);

    view = new HeatMapView(this);
    view->setObjectName("heatMapView");
    view->setFont(font());
    // setup buttons and menu
    yearBtn = new QPushButton(QString::number(view->getYear()), this);
    yearBtn->setObjectName("heatMapBtn");
    yearBtn->setSizePolicy(QSizePolicy::Maximum, QSizePolicy::Maximum);
    yearBtn->setFocusPolicy(Qt::TabFocus);
    yearBtn->setFont(font());
    connect(yearBtn, &QPushButton::clicked, this, [&](){
        // Popup menu manually to avoid indicator in YearButton
        yearMenu->exec(yearBtn->mapToGlobal(QPoint(0, yearBtn->height())));
    });

    yearMenu = new QMenu(this);
    yearMenu->setObjectName("heatMapMenu");
    setupYearMenu();

    auto sz = QSize(16, 16) * scaleRatio;
    auto preBtn = new QToolButton(this);
    preBtn->setIcon(makeQIcon(":/heatmap/arrow-left.png", true));
    preBtn->setIconSize(sz);
    connect(preBtn, &QToolButton::clicked, this, &HeatMap::yearPre);
    auto nextBtn = new QToolButton(this);
    nextBtn->setIcon(makeQIcon(":/heatmap/arrow-right.png", true));
    nextBtn->setIconSize(sz);
    connect(nextBtn, &QToolButton::clicked, this, &HeatMap::yearNext);

    // setup color sample
    sample = new ColorSampleView(this, 11);
    // without following size will be bigger than fixed, why?
    sample->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
    sample->setFixedSize(200, 14*scaleRatio);
    barLayout->addWidget(preBtn);
    barLayout->addWidget(nextBtn);
    barLayout->addSpacing(200 - preBtn->sizeHint().width()*2 - barLayout->spacing());
    barLayout->addStretch();
    barLayout->addWidget(yearBtn);
    barLayout->addStretch();
    barLayout->addWidget(sample);
    layout->addWidget(bar);
    layout->addWidget(view);
    // setup shortcuts
    new QShortcut(QKeySequence(Qt::Key_Left), this, SLOT(yearPre()));
    new QShortcut(QKeySequence(Qt::Key_Right), this, SLOT(yearNext()));
    new QShortcut(QKeySequence(Qt::Key_Up), this, SLOT(yearPre5()));
    new QShortcut(QKeySequence(Qt::Key_Down), this, SLOT(yearNext5()));
    new QShortcut(QKeySequence(Qt::Key_Escape), this, SLOT(close()));
}

void HeatMap::showEvent(QShowEvent *e) {
    Q_UNUSED(e);
    // must call setupMap after style polished
    view->setupMap();
    sample->setColors(view->getCellColors());
    sample->setupMap();
}

void HeatMap::moveYear(int offset) {
    view->setYear(view->getYear() + offset);
    yearBtn->setText(QString::number(view->getYear()));
    setupYearMenu();
}

void HeatMap::setupYearMenu() {
    yearMenu->clear();
    auto group = new QActionGroup(yearMenu);
    int curtYear = view->getYear();
    std::function<QAction*(int)> newAct = [&](int y) {
        auto a = new QAction(QString::number(y), group);
        connect(a, &QAction::triggered, this, &HeatMap::yearMenuAct);
        yearMenu->addAction(a);
        return a;
    };

    newAct(curtYear-10);
    newAct(curtYear-7);
    yearMenu->addSeparator();
    for (int i : range(curtYear-4, curtYear))
        newAct(i);

    auto curtYearAc = newAct(curtYear);
    curtYearAc->setDisabled(true);
    curtYearAc->setCheckable(true);
    curtYearAc->setChecked(true);

    for (int i : range(curtYear+1, curtYear+5))
        newAct(i);
    yearMenu->addSeparator();
    newAct(curtYear+7);
    newAct(curtYear+10);
}

void HeatMap::yearMenuAct() {
    int y = qobject_cast<QAction*>(sender())->text().toInt();
    moveYear(y-view->getYear());
}


ColorSampleView::ColorSampleView(QWidget *parent, int cellLen) : QGraphicsView(parent) {
    setObjectName("heatMapSample");
    setAlignment(Qt::AlignRight);
    colors = defCellColors;
    this->cellLen = (cellLen == -1) ? 9 : cellLen;
    descriptions = QStringList({"", "", "", ""});

    setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    auto scene = new QGraphicsScene(this);
    scene->setSceneRect(0, 0, cellLen*colors.length(), cellLen);
    setScene(scene);
}

void ColorSampleView::setupMap() {
    QPen borderPen(Qt::darkGray);
    borderPen.setWidth((scaleRatio <= 1.5) ? 1 : 2);
    borderPen.setCosmetic(true);
    for (int i : range(colors.length())) {
        auto item = new QGraphicsRectItem(cellLen*i, 0, cellLen, cellLen);
        item->setToolTip(descriptions[i]);
        item->setPen(borderPen);
        item->setBrush(colors[i]);
        scene()->addItem(item);
    }
}

void ColorSampleView::resizeEvent(QResizeEvent *e) {
    Q_UNUSED(e);
    fitInView(scene()->sceneRect(), Qt::KeepAspectRatio);
}

// Set colors to display, arg colors is a list of QColor
void ColorSampleView::setColors(const QList<QColor> &colors) {
    this->colors = colors.toVector();
    // update scene rect if colors.length changed
}

void ColorSampleView::setDescriptions(QStringList seq) {
    Q_ASSERT(seq.length() == colors.length());
    descriptions = seq;
}
