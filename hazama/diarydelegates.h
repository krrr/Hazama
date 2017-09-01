#pragma once
#include <QAbstractItemDelegate>
#include "customobjects/ntextdocument.h"

class ColorfulDiaryItem;


/* ItemDelegate of old theme 'one-pixel-rect' for DiaryList, Using 'traditional'
   painting method compared to colorful theme */
class DiaryDelegate : public QAbstractItemDelegate {
public:
    DiaryDelegate(QObject *parent=nullptr);
    void paint(QPainter *p, const QStyleOptionViewItem &opt, const QModelIndex &idx) const;
    QSize sizeHint(const QStyleOptionViewItem &opt,const QModelIndex &idx) const;

private:
    int titleH, titleAreaH, textH, tagPathH, tagH, dtW;
    QColor textC, bgC, borderC, inActBgC, grayC;
    NTextDocument *doc;
};

/* ItemDelegate of theme 'colorful' for DiaryList. Using widget rendering. */
class DiaryDelegateColorful : public QAbstractItemDelegate {
public:
    DiaryDelegateColorful(QObject *parent=nullptr);
    void paint(QPainter *p, const QStyleOptionViewItem &opt, const QModelIndex &idx) const;
    QSize sizeHint(const QStyleOptionViewItem &opt,const QModelIndex &idx) const;
    ~DiaryDelegateColorful();

private:
    static const QString TAG_SEPARATOR;
    int itemHeightWithTag, itemHeightNoTag;
    ColorfulDiaryItem *itemWidget;
};
