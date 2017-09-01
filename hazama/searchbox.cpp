#include <QPushButton>
#include <QShortcut>
#include <QTimer>
#include "searchbox.h"


SearchBox::SearchBox(QWidget *parent) : QLineEditWithMenuIcon(parent) {
    setObjectName("searchBox");

    btn = new QPushButton(this);
    btn->setObjectName("searchBoxBtn");
    auto sz = QSize(16, 16) * scaleRatio;
    btn->setFocusPolicy(Qt::NoFocus);
    btn->setFixedSize(sz);
    btn->setIconSize(sz);
    btn->setCursor(Qt::PointingHandCursor);
    connect(btn, &QPushButton::clicked, this, &SearchBox::onBtnClicked);

    auto gr = new QActionGroup(this);
    byTitleTextAct = new QAction(tr("Title && Text"), gr);
    byDatetimeAct = new QAction(tr("Date (YYYY-MM-DD)"), gr);
    for (auto i : {byTitleTextAct, byDatetimeAct})
        i->setCheckable(true);
    byTitleTextAct->setChecked(true);

    clearSc = new QShortcut(QKeySequence(Qt::Key_Escape), this);
    connect(clearSc, &QShortcut::activated, this, &SearchBox::clear);

    connect(this, &SearchBox::textChanged, this, &SearchBox::onTextChanged);
    setMinimumHeight(btn->height() * 1.2);
    setTextMargins(QMargins(2, 0, 16, 0));

    searchIco = makeQIcon(":/search.png", true);
    clrIco = makeQIcon(":/search-clr.png", true);
    retranslate();
    onTextChanged("");  // initialize the icon

    delayed = new QTimer(this);
    delayed->setSingleShot(true);
    delayed->setInterval(310);
    connect(delayed, &QTimer::timeout, [this](){ emit contentChanged(text()); });
    connect(this, &SearchBox::textChanged, this, &SearchBox::updateDelayedTimer);
}

void SearchBox::resizeEvent(QResizeEvent *e) {
    int pos_y = (e->size().height() - btn->height()) / 2;
    btn->move(e->size().width() - btn->width() - pos_y, pos_y);
}

void SearchBox::retranslate() {
    searchByTip = tr("Click to change search option");
    setPlaceholderText(tr("Search"));
}

void SearchBox::updateDelayedTimer(QString text) {
    if (text.isEmpty())  {  // fast clear
        delayed->stop();
        emit contentChanged("");  // delay this call is not a good idea
    } else
        delayed->start();  // restart if already started
}

void SearchBox::onBtnClicked() {
    if (hasText)
        return clear();

    QMenu menu;
    menu.addActions({byTitleTextAct, byDatetimeAct});
    menu.exec(btn->mapToGlobal(QPoint(0, btn->height())));
}

void SearchBox::onTextChanged(QString text) {
    if (hasText == !text.isEmpty())
        return;
    btn->setIcon((text.isEmpty() ? searchIco : clrIco));
    btn->setToolTip((text.isEmpty() ? searchByTip : ""));
    hasText = !text.isEmpty();
}
