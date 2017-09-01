#pragma once
#include <QLabel>
#include <QPainter>
#include <QPaintEvent>


class ElideLabel : public QLabel {
public:
    Qt::TextElideMode elideMode = Qt::ElideRight;

    using QLabel::QLabel;

    void paintEvent(QPaintEvent *e) {
        QPainter p(this);
        p.setClipRegion(e->region());
        auto rect = contentsRect();
        auto txt = fontMetrics().elidedText(text(), elideMode, rect.width());
        p.drawText(rect, alignment(), txt);
    }

    QSize minimumSizeHint() const { return QSize(); }
};
