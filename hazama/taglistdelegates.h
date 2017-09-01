#pragma once
#include <QItemDelegate>

class ColorfulItem;


class TagDelegateBase : public QItemDelegate {
    using QItemDelegate::QItemDelegate;

public:
    void updateEditorGeometry(QWidget *editor, const QStyleOptionViewItem &opt, const QModelIndex &idx) const;
    QWidget *createEditor(QWidget *parent, const QStyleOptionViewItem &opt, const QModelIndex &idx) const;
};


class TagDelegate : public TagDelegateBase {
public:
    TagDelegate(QObject *parent=nullptr);
    void paint(QPainter *p, const QStyleOptionViewItem &opt, const QModelIndex &idx) const;
    QSize sizeHint(const QStyleOptionViewItem &opt,const QModelIndex &idx) const;
    void updateEditorGeometry(QWidget *editor, const QStyleOptionViewItem &opt, const QModelIndex &idx) const;

private:
    int h;
    bool showCount;
};


/* ItemDelegate of theme 'colorful' for TagList. Using widget rendering. */
class TagDelegateColorful : public TagDelegateBase {
public:
    TagDelegateColorful(QObject *parent=nullptr);
    ~TagDelegateColorful();
    void paint(QPainter *p, const QStyleOptionViewItem &opt, const QModelIndex &idx) const;
    QSize sizeHint(const QStyleOptionViewItem &opt,const QModelIndex &idx) const;

private:
    ColorfulItem *itemWidget;
    bool showCount;
};
