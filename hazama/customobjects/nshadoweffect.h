#pragma once
#include <QGraphicsDropShadowEffect>

/* Adjust strength of effect simply by drawing multiple times. */
class NShadowEffect : public QGraphicsDropShadowEffect {
public:
    NShadowEffect(int times=1, QObject *parent=nullptr);
    void draw(QPainter *p);
private:
    int times;
};
