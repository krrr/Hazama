#pragma once
#include <QListWidget>

class QShortcut;



class TagList : public QListWidget {
    Q_OBJECT
public:
    TagList(QWidget *parent=nullptr);
    void load();
    void reload();
    void showAndLoad() { load(); show(); }

signals:
    void currentTagChanged(QString tagName);  // empty when "All" selected
    void tagNameModified(QString tagName);

protected:
    void hideEvent(QHideEvent *e);
    void contextMenuEvent(QContextMenuEvent *e);
    void commitData(QWidget *editor);

private:
    QShortcut *nextSc, *preSc;

    void setupDelegate();
};
