#include <algorithm>
#include <QMenu>
#include <QSortFilterProxyModel>
#include <QContextMenuEvent>
#include <QScrollBar>
#include "globals.h"
#include "diarylistscrollbar.h"
#include "diarylist.h"
#include "diarydelegates.h"
#include "diarymodel.h"


// bug: jumped to selected item after deselect any tag
// reproduce: click an item with any tag selected in tag list, and then click ALL tag fast enough (< 100ms)
// reason: Qt's autoScroll feature will ensure currentIndex is fully visible

class ProxyModel : public QSortFilterProxyModel {
public:
    QString tag, search, datetime;  // search and datetime are exclusive
    using QSortFilterProxyModel::QSortFilterProxyModel;

    bool filterAcceptsRow(int row, const QModelIndex &) const {
        if (!hasFilter())
            return true;

        auto diary = sourceModel()->index(row, 0).data().value<Diary>();
        if (!tag.isEmpty() && diary.tags.contains(tag))
            return true;
        if (!search.isEmpty() && (diary.title.contains(search, Qt::CaseInsensitive) ||
                                  diary.text.contains(search, Qt::CaseInsensitive)))
            return true;
        if (!datetime.isEmpty() && (diary.datetime.toString(Qt::ISODate).contains(datetime)))
            return true;
        return false;
    }

    bool lessThan(const QModelIndex &left, const QModelIndex &right) const {
        auto dLeft = left.data().value<Diary>();
        auto dRight = right.data().value<Diary>();
        switch (sortBy) {
        case SortBy::Length:
            return dLeft.text.size() < dRight.text.size();
        case SortBy::Title:
            return dLeft.title < dRight.title;
        case SortBy::Datetime:
            return dLeft.datetime < dRight.datetime;
        }
        Q_UNREACHABLE();
    }

    void setSortBy(const QString &by) {
        auto it = std::find(std::begin(strs), std::end(strs), by);
        Q_ASSERT(it != std::end(strs));
        sortBy = static_cast<SortBy>(it - std::begin(strs));
        invalidate();
    }

    bool hasFilter() const {
        return !(tag.isEmpty() && search.isEmpty() && datetime.isEmpty());
    }

private:
    enum class SortBy { Length, Title, Datetime };
    static const QStringList strs;
    SortBy sortBy;
};
const QStringList ProxyModel::strs = {"length", "title", "datetime"};


DiaryList::DiaryList(QWidget *parent) : QListView(parent) {
    setupDelegate();

    auto sb = new DiaryListScrollBar(this);
    setVerticalScrollBar(sb);
    originModel = new DiaryModel(this);
    proxyModel = new ProxyModel(this);
    proxyModel->setSourceModel(originModel);
    proxyModel->setDynamicSortFilter(true);
    connect(sb, &DiaryListScrollBar::yearMenuClicked, [&](QModelIndex i){
        setCurrentIndex(proxyModel->mapFromSource(i));
    });
    setModel(proxyModel);
    sort();
    connect(proxyModel, &ProxyModel::layoutChanged, sb, &DiaryListScrollBar::onModelChanged);

    editAct = new QAction(tr("Edit"), this);
    delAct = new QAction(makeQIcon(":/menu/list-delete.png", true), tr("Delete"), this);
    delAct->setShortcut(QKeySequence::Delete);
    randAct = new QAction(makeQIcon(":/menu/random-big.png", true), tr("Random"), this);
    randAct->setShortcut(QKeySequence(Qt::Key_F7));
    connect(randAct, &QAction::triggered, this, &DiaryList::gotoRandomRow);
    gotoAct = new QAction(tr("Go to location"), this);

    addActions({editAct, delAct, randAct, gotoAct});
}

void DiaryList::contextMenuEvent(QContextMenuEvent *e) {
    QMenu menu;
    menu.addAction(editAct);
    menu.addAction(delAct);
    menu.addSeparator();
    menu.addAction(randAct);

    int selCount = selectedIndexes().size();
    if (selCount == 1 && proxyModel->hasFilter())
        menu.addAction(gotoAct);
    editAct->setDisabled(selCount != 1);
    delAct->setDisabled(selCount == 0);
    randAct->setDisabled(model()->rowCount() == 0);
    menu.exec(e->globalPos());
}

void DiaryList::load() {
    emit startLoading();
    auto yearFirsts = originModel->populate();
    emit countChanged();

    // set annotated scrollbar
    auto sb = static_cast<DiaryListScrollBar*>(verticalScrollBar());
    std::reverse(yearFirsts.begin(), yearFirsts.end());  // only annotate when list reversed
    if (settings->value("listAnnotated").toBool()) {
        QVector<QPersistentModelIndex> indexes;
        for (int r : yearFirsts)
            indexes.append(originModel->index(r));
        sb->setPositions(indexes, static_cast<QSortFilterProxyModel*>(proxyModel));
    }
}

void DiaryList::saveDiary(const Diary &diary, bool ignoreTags) {
    int row = originModel->saveDiary(diary, ignoreTags);
    clearSelection();
    setCurrentIndex(proxyModel->mapFromSource(originModel->index(row, 0)));
}

void DiaryList::deleteSelected() {
    auto indexes = selectedIndexes();
    // delete will invalidate indexes after the deleted one
    std::sort(indexes.begin(), indexes.end(), [](auto a, auto b){ return a.row() >= b.row(); });
    for (auto i : indexes)
        originModel->deleteDiary(proxyModel->mapToSource(i).row());
}

void DiaryList::setupDelegate() {
    auto theme = settings->value("theme").toString();
    if (theme == "colorful")
        setItemDelegate(new DiaryDelegateColorful(this));
    else
        setItemDelegate(new DiaryDelegate(this));
    if (isVisible())
        setSpacing(spacing());  // force items to be laid again
}

void DiaryList::sort() {
    proxyModel->setSortBy(settings->value("listSortBy").toString());
    auto reverse = settings->value("listReverse").toBool();
    proxyModel->sort(0, (reverse) ? Qt::DescendingOrder : Qt::AscendingOrder);
}

void DiaryList::setFilterBySearchStr(const QString &s) {
    proxyModel->datetime.clear();
    proxyModel->search = s;
    proxyModel->invalidate();
}

void DiaryList::setFilterByTag(const QString &s) {
    proxyModel->tag = s;
    proxyModel->invalidate();
}

void DiaryList::setFilterByDatetime(const QString &s) {
    proxyModel->search.clear();
    proxyModel->datetime = s;
    proxyModel->invalidate();
}

void DiaryList::refreshFilteredTags(const QString &newTagName) {
    setFilterByTag(newTagName);
}

void DiaryList::gotoRow(int row) {
    setCurrentIndex(model()->index(row, 0));
}

void DiaryList::gotoRandomRow() {
    gotoRow(qrand() % model()->rowCount());
}
