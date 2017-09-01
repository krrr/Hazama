#pragma once
#include <functional>
#include <QWidget>
#include <QGraphicsView>

class QGraphicsScene;
class QPushButton;
class QMenu;


class HeatMapView : public QGraphicsView {
    Q_OBJECT
    Q_PROPERTY(int year READ getYear WRITE setYear)
    Q_PROPERTY(QColor cellBorderColor MEMBER cellBorderColor)
    Q_PROPERTY(QColor cellColor0 MEMBER cellColor0)
    Q_PROPERTY(QColor cellColor1 MEMBER cellColor1)
    Q_PROPERTY(QColor cellColor2 MEMBER cellColor2)
    Q_PROPERTY(QColor cellColor3 MEMBER cellColor3)
public:
    static const int cellLen = 9;
    static const int cellSpacing = 2;
    static const int monthSpacingX = 14;
    static const int monthSpacingY = 20;
    static const int nameFontPx = 9;  // month name
    QColor cellColor0, cellColor1, cellColor2, cellColor3;
    std::function<QColor(int, const QList<QColor>&)> cellColorFunc;  // (data, cellColors)
    std::function<int(QDate)> cellDataFunc;  // (y, m, d)

    HeatMapView(QWidget *parent=nullptr);
    QList<QColor> getCellColors() { return { cellColor0, cellColor1, cellColor2, cellColor3 }; }
    void resizeEvent(QResizeEvent *e);
    void setupMap();
    int getYear() { return year; }
    void setYear(int y);

private:
    int year;
    QColor cellBorderColor = Qt::lightGray;
    int cellDis, monthDisX, monthDisY;
};


class ColorSampleView : public QGraphicsView {
public:
    ColorSampleView(QWidget *parent=nullptr, int cellLen=-1);
    void setupMap();
    void resizeEvent(QResizeEvent *e);
    void setColors(const QList<QColor> &colors);
    void setDescriptions(QStringList seq);

private:
    int cellLen;
    QVector<QColor> colors;
    QStringList descriptions;
};


class HeatMap : public QWidget {
    Q_OBJECT
public:
    QPushButton *yearBtn;
    ColorSampleView *sample;
    HeatMapView *view;

    HeatMap(QWidget *parent=nullptr);
    void showEvent(QShowEvent *e);

private:
    QMenu *yearMenu;

    void setupYearMenu();

public slots:
    void moveYear(int offset);
    void yearPre() { moveYear(-1); }
    void yearNext() { moveYear(1); }
    void yearPre5() { moveYear(-5); }
    void yearNext5() { moveYear(5); }
    void yearMenuAct();
};
