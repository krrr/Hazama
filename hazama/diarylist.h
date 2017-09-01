#pragma once
#include <QListView>

class DiaryModel;
class ProxyModel;
struct Diary;


class DiaryList : public QListView {
    Q_OBJECT
public:
    QAction *editAct, *delAct, *gotoAct;

    DiaryList(QWidget *parent=nullptr);
    void contextMenuEvent(QContextMenuEvent *e);
    void load();
    void gotoRow(int row);
    void sort();
    void setupDelegate();
    void saveDiary(const Diary &diary, bool ignoreTags);
    void deleteSelected();
    bool hasSelection() { return !selectedIndexes().isEmpty(); }

signals:
    void startLoading();
    void countChanged();

public slots:
    void setFilterBySearchStr(const QString &s);
    void setFilterByTag(const QString &s);
    void setFilterByDatetime(const QString &s);
    void refreshFilteredTags(const QString &newTagName);

private:
    QMenu *menu;
    QAction *randAct;
    DiaryModel *originModel;
    ProxyModel *proxyModel;

    void gotoRandomRow();
};
