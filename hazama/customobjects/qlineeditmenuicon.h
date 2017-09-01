#pragma once
#include <QLineEdit>
#include <QContextMenuEvent>
#include <QMenu>
#include "globals.h"

/* QLineEdit with system theme icons in context menu */
class QLineEditWithMenuIcon : public QLineEdit {
public:
    QLineEditWithMenuIcon(QWidget *parent=nullptr) : QLineEdit(parent) {}

    void contextMenuEvent(QContextMenuEvent *e) {
        auto menu = createStandardContextMenu();
        setStdEditMenuIcons(menu);
        menu->exec(e->globalPos());
        menu->deleteLater();
    }
};
