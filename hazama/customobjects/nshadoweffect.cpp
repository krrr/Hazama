#include "nshadoweffect.h"
#include "globals.h"

NShadowEffect::NShadowEffect(int times, QObject *parent) :
    QGraphicsDropShadowEffect(parent), times(times) {}

void NShadowEffect::draw(QPainter *p) {
    for (int _ : range(times))
        QGraphicsDropShadowEffect::draw(p);
}
