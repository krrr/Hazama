#include "diarylistscrollbar.h"
#include <QContextMenuEvent>
#include <QSortFilterProxyModel>
#include <QMenu>
#include <QPainter>
#include <QStyleOptionSlider>
#include <QStyle>
#include "diarymodel.h"
#include "globals.h"

static inline
bool shouldAnnotate() {
    return settings->value("listSortBy").toString() == "datetime" &&
        settings->value("listReverse").toBool();
}


DiaryListScrollBar::DiaryListScrollBar(QWidget *parent) : QScrollBar(parent) {
    setObjectName("diaryListSB");
    _color = QColor("gold");
}

void DiaryListScrollBar::contextMenuEvent(QContextMenuEvent *e) {
    if (!annotated)
        return;
    QMenu menu;
    QAction hint(tr("Go to the first diary of each year"), nullptr);
    hint.setEnabled(false);
    menu.addAction(&hint);
    menu.addSeparator();
    for (auto &i : pairs) {
        if (i.first < 0)
            continue;
        auto act = new QAction(QString::number(i.first), &menu);
        connect(act, &QAction::triggered, [&]() { emit yearMenuClicked(i.second); });
        menu.addAction(act);
    }
    menu.exec(e->globalPos());
}

void DiaryListScrollBar::paintEvent(QPaintEvent *e) {
    QScrollBar::paintEvent(e);
    if (poses.isEmpty() || !annotated)
        return;
    QPainter p(this);
    // avoid painting on slider handle
    QStyleOptionSlider opt;
    initStyleOption(&opt);
    auto groove = style()->subControlRect(QStyle::CC_ScrollBar, &opt,
                                          QStyle::SC_ScrollBarGroove, this);
    auto slider = style()->subControlRect(QStyle::CC_ScrollBar, &opt,
                                          QStyle::SC_ScrollBarSlider, this);
    p.setClipRegion(QRegion(groove) - QRegion(slider), Qt::IntersectClip);

    int x = groove.x() + 1;
    int w = groove.width() - 2;
    int h = 3 * scaleRatio;
    auto c = _color;
    c.setAlpha(70);
    p.setBrush(c);
    c.setAlpha(145);
    p.setPen(QPen(c, scaleRatio));
    for (int i : range(poses.size()-1))
        p.drawRect(x, groove.y()+groove.height()*poses[i], w, h);
    // the last may intersect with bottom of groove
    int lastY = groove.y()+groove.height()*poses[poses.size()-1];
    if (lastY + h >= groove.bottom())
        lastY -= 3 * scaleRatio;
    p.drawRect(x, lastY, w, h);
}

void DiaryListScrollBar::setPositions(const QVector<QPersistentModelIndex> &indexes,
                                      QSortFilterProxyModel *proxyModel) {
    annotated = shouldAnnotate();
    poses.clear();
    pairs.clear();
    if (indexes.isEmpty())
        return;

    this->proxyModel = proxyModel;
    double rowCount = proxyModel->rowCount();
    for (auto &i : indexes) {
        int year = i.data().value<Diary>().datetime.date().year();
        poses.append(proxyModel->mapFromSource(i).row() / rowCount);
        pairs.append(qMakePair(year, i));
    }
}

void DiaryListScrollBar::onModelChanged() {
    logD()<<__FUNCTION__;
    annotated = shouldAnnotate();
    update();
    if (poses.isEmpty() || !annotated)
        return;

    for (int i : range(pairs.size())) {
        const auto &idx = pairs[i].second;
        if (proxyModel->mapFromSource(idx).isValid()) {
            if (pairs[i].first < 0)
                pairs[i].first = -pairs[i].first;
            poses[i] = idx.row() / double(idx.model()->rowCount());
        } else  { // may be deleted or filtered, make it visually hidden
            pairs[i].first = -pairs[i].first;
            poses[i] = 2;
        }
    }
}
