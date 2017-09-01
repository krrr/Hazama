#include "taglist.h"
#include <QListWidgetItem>
#include <QShortcut>
#include <QMenu>
#include <QLineEdit>
#include <QContextMenuEvent>
#include "diarymodel.h"
#include "globals.h"
#include "db.h"
#include "taglistdelegates.h"

// tag list is simple, so don't use custom model
QVector<QPair<QString, int>> dbTags(bool getCount) {
    QVector<QPair<QString, int>> ret;
    QSqlQuery q;
    if (getCount)
        q.prepare("SELECT Tags.name, (SELECT COUNT(*) FROM Nikki_Tags "
                  "WHERE Nikki_Tags.tagid=Tags.id) AS count FROM Tags");
    else
        q.prepare("SELECT name FROM Tags");
    q.exec();
    while (q.next())
        ret.append(qMakePair(q.value(0).toString(), q.value(1).toInt()));
    return ret;
}


TagList::TagList(QWidget *parent) : QListWidget(parent) {
    nextSc = new QShortcut(QKeySequence("Ctrl+Tab"), this);
    connect(nextSc, &QShortcut::activated, [&](){ setCurrentRow((currentRow()+1) % count()); });
    preSc = new QShortcut(QKeySequence("Ctrl+Shift+Tab"), this);  // QKeySequence::PreviousChild has bug
    connect(preSc, &QShortcut::activated, [&](){ setCurrentRow((currentRow()-1+count()) % count()); });

    connect(this, &TagList::currentItemChanged, [&](QListWidgetItem *i) {
        // i become null after hiding the list
        emit currentTagChanged((i==nullptr || i==item(0)) ? "" : i->data(Qt::DisplayRole).toString());
    });
    setupDelegate();
}

void TagList::hideEvent(QHideEvent *) {
    clear();
}

void TagList::contextMenuEvent(QContextMenuEvent *e) {
    auto idx = currentIndex();
    if (idx.row() == 0)  // ignore "All" item. cursor must over the item
        return;
    QMenu menu;
    QAction rename(tr("Rename"), nullptr);
    connect(&rename, &QAction::triggered, [&](){ edit(idx); });
    menu.addAction(&rename);
    menu.exec(e->globalPos());
}

void TagList::commitData(QWidget *editor) {
    auto edit = qobject_cast<QLineEdit*>(editor);
    auto newName = edit->text();
    auto oldName = edit->property("oldText").toString();  // oldText is set in delegate's createEditor
    if (edit->isModified() && !newName.isEmpty() && !newName.contains(' ')) {
        DiaryModel::instance->changeTagName(oldName, newName);
        logI().quote() << "tag" << oldName << "changed to" << newName;
        QListWidget::commitData(editor);  // it will call delegate's setModelData
        emit tagNameModified(newName);
    }
}

void TagList::load() {
    Q_ASSERT(count() == 0);
    logD() << "load Tag List";
    new QListWidgetItem(tr("All"), this);
    setCurrentRow(0);

    bool getCount = settings->value("tagListCount").toBool();
    for (auto i : dbTags(getCount)) {
        auto item = new QListWidgetItem(i.first, this);
        item->setFlags(Qt::ItemIsEditable | Qt::ItemIsSelectable | Qt::ItemIsEnabled);
        item->setData(Qt::ToolTipRole, i.first);
        if (getCount)
            item->setData(Qt::UserRole, i.second);
    }
}

void TagList::reload() {
    if (!isVisible())
        return;
    auto currentTag = (currentItem() == nullptr) ? "" : currentItem()->data(Qt::DisplayRole).toString();
    clear();
    load();
    if (!currentTag.isEmpty()) {
        auto i = findItems(currentTag, Qt::MatchFixedString);
        setCurrentItem((i.isEmpty()) ? item(0) : i[0]);
    }
}

void TagList::setupDelegate() {
    auto theme = settings->value("theme").toString();
    if (theme == "colorful")
        setItemDelegate(new TagDelegateColorful(this));
    else
        setItemDelegate(new TagDelegate(this));
    if (isVisible())
        setSpacing(spacing());  // force items to be laid again
}
