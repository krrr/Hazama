#pragma once
#include <QScrollBar>
#include <QPointer>
#include <QSortFilterProxyModel>


/* Annotated scrollbar */
class DiaryListScrollBar : public QScrollBar {
    Q_OBJECT
public:
    Q_PROPERTY(QColor annotateColor MEMBER _color)

    DiaryListScrollBar(QWidget *parent=nullptr);
    /* Used to jump to the first day of years. Original menu is almost useless. */
    void contextMenuEvent(QContextMenuEvent *e);
    void paintEvent(QPaintEvent *e);
    void setPositions(const QVector<QPersistentModelIndex> &indexes,
                      QSortFilterProxyModel *proxyModel);

signals:
    void yearMenuClicked(QModelIndex idx);

public slots:
    void onModelChanged();

private:
    bool annotated;
    QColor _color;
    QPointer<QSortFilterProxyModel> proxyModel;
    QVector<QPair<int, QPersistentModelIndex>> pairs;  // (year, index)
    QVector<double> poses;  // (row / rowCount) of marks, roughly equal to (y / scrollBarGroveHeight)
};
