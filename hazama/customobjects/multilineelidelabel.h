#pragma once
#include <QFrame>

class QTextLayout;

/* Qt Widget version of QML text.maximumLineCount */
class MultiLineElideLabel : public QFrame {
public:
    QChar elideMark = QChar(0x2026);

    MultiLineElideLabel(QWidget *parent=nullptr, bool forceHeightHint=true);
    void resizeEvent(QResizeEvent *event);
    void setFont(const QFont &f);
    QSize sizeHint() const;
    void paintEvent(QPaintEvent *event);
    void setText(QString text);
    void setMaximumLineCount(int lines);

private:
    bool forceHeightHint;
    int maximumLineCount = 4;
    QTextLayout layout;
    QString text;
    int elideMarkWidth;
    QPoint elideMarkPos;
    int heightHint, lineHeight, realHeight;

    void updateSize();
    void setupLayout();
};
