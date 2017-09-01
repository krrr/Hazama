#pragma once
#include "customobjects/qlineeditmenuicon.h"

class QPushButton;
class QShortcut;

/* The real-time search box in toolbar. contentChanged signal will be
 * delayed after textChanged, it prevent lagging when text changing quickly
 * and the amount of data is large.*/
class SearchBox: public QLineEditWithMenuIcon {
    Q_OBJECT
public:
    QAction *byTitleTextAct, *byDatetimeAct;

    SearchBox(QWidget *parent=nullptr);
    void resizeEvent(QResizeEvent *e);
    void retranslate();

signals:
    void contentChanged(QString content);  // replace textChanged

private:
    QPushButton *btn;
    QShortcut *clearSc;
    bool hasText = true;
    QIcon searchIco, clrIco;
    QTimer *delayed;
    QString searchByTip;

private slots:
    void updateDelayedTimer(QString text);
    void onBtnClicked();
    void onTextChanged(QString text);
};
