#include "diarymodel.h"
#include "globals.h"
#include "db.h"

DiaryModel *DiaryModel::instance = nullptr;


static inline
QSqlQuery execute(const QString &sql, ilist<QVariant> values={}) {
    QSqlQuery q(sql);
    q.setForwardOnly(true);
    for (auto i : values)
        q.addBindValue(i);
    q.exec();
    return q;
}

static inline
QVariant executeOne(const QString &sql, ilist<QVariant> values={}) {
    auto q = execute(sql, values);
    q.next();
    return (q.isValid()) ? q.value(0) : QVariant();
}

// return diaryId -> list of tags
QHash<int, QStringList> dbDiaryTags() {
    QHash<int, QString> tagId2Name;
    auto q = execute("SELECT * FROM tags");
    while (q.next())
        tagId2Name[q.value(0).toInt()] = q.value(1).toString();

    QHash<int, QStringList> ret;
    q = execute("SELECT * FROM nikki_tags");
    while (q.next())
        ret[q.value(0).toInt()].append(tagId2Name[q.value(1).toInt()]);
    return ret;
}

// return diaryId -> list of formats
QHash<int, QVector<Diary::TextFormat>> dbDiaryFormats() {
    QHash<int, QVector<Diary::TextFormat>> ret;
    auto q = execute("SELECT * FROM TextFormat");
    while (q.next())
        ret[q.value(0).toInt()].append({
                q.value(1).toInt(), q.value(2).toInt(),
                static_cast<Diary::TextFormat::Type>(q.value(3).toInt())});
    return ret;
}

// Get tag-id by name, because TagList doesn't store id (lazy).
int getTagId(const QString &name) {
    auto v = executeOne("SELECT id FROM Tags WHERE name=?", {name});
    return (v.isValid()) ? v.toInt() : -1;
}

DiaryModel::DiaryModel(QObject *parent) : QAbstractListModel(parent) {
    Q_ASSERT(!instance);
    instance = this;
}

DiaryModel::~DiaryModel(){
    instance = nullptr;
}

int DiaryModel::rowCount(const QModelIndex &) const {
    return list.size();
}

QVariant DiaryModel::data(const QModelIndex &index, int role) const {
    if (role != Qt::DisplayRole || index.row() < 0 || index.row() >= list.size())
        return {};
    return QVariant::fromValue(list[index.row()]);
}

bool DiaryModel::setData(const QModelIndex &index, const QVariant &value, int role) {
    if (role != Qt::DisplayRole || index.row() < 0 || index.row() >= list.size())
        return false;
    list[index.row()] = value.value<Diary>();
    emit dataChanged(index, index);
    return true;
}

bool DiaryModel::insertRows(int row, int count, const QModelIndex &) {
    beginInsertRows(QModelIndex(), row, row+count-1);
    list.insert(row, count, {});
    endInsertRows();
    return true;
}

bool DiaryModel::removeRows(int row, int count, const QModelIndex &) {
    Q_ASSERT(row >= 0 && row < list.size());
    beginRemoveRows(QModelIndex(), row, row+count-1);
    list.remove(row, count);
    endRemoveRows();
    return true;
}

void DiaryModel::deleteDiary(int row) {
    execute("DELETE FROM Nikki WHERE id = ?", {list[row].id});
    qInfo("diary deleted (ID: %d)", list[row].id);
    // tag data will be deleted automatically by trigger
    removeRow(row);
}

int DiaryModel::saveDiary(const Diary &diary, bool ignoreTags, bool batch) {
    bool newDiary = diary.id == -1;
    //// write to database
    if (!batch)
        database()->transaction();
    int id = diary.id;
    if (newDiary) {
        auto q = execute("INSERT INTO Nikki VALUES(NULL, ?, ?, ?)",
                         {diary.datetime.toString(DB_DATETIME_FMT), diary.text, diary.title});
        Q_ASSERT(q.lastInsertId().isValid());
        id = q.lastInsertId().toInt();
    } else {
        execute("UPDATE Nikki SET datetime=?, text=?, title=? WHERE id=?",
                {diary.datetime.toString(DB_DATETIME_FMT), diary.text, diary.title, id});
    }
    // formats processing
    if (!newDiary)  // delete existing format information
        execute("DELETE FROM TextFormat WHERE nikkiid=?", {id});
    for (auto i : diary.formats)
        execute("INSERT INTO TextFormat VALUES(?,?,?,?)", {id, i.index, i.length, (int)i.type});
    // tags processing
    if (!ignoreTags) {
        if (newDiary)  // delete existing tags first
            execute("DELETE FROM Nikki_Tags WHERE nikkiid=?", {id});
        for (auto t : diary.tags) {
            int tagId = getTagId(t);
            if (tagId == -1) {
                execute("INSERT INTO Tags VALUES(NULL,?)", {t});
                tagId = getTagId(t);
                Q_ASSERT(tagId != -1);
            }
            execute("INSERT INTO Nikki_Tags VALUES(?,?)", {id, tagId});
        }
    }

    if (!batch) {
        database()->commit();
        qInfo("diary saved (ID:%d)", id);
    }

    //// write to model
    int row;
    if (newDiary) {
        row = list.size();
        insertRow(row);
        list[row] = diary;
        list[row].id = id;
    } else {
        row = getRowById(id);
        list[row] = diary;
    }
    emit dataChanged(index(row, 0), index(row, 0));
    return row;
}

int DiaryModel::getRowById(int id) {
    // naive; user tends to modify newer diaries?
    for (int i : range(list.size()-1, 0, -1))
        if (list[i].id == id)
            return i;
    return -1;
}

QVector<int> DiaryModel::populateDummy() {
    beginInsertRows(QModelIndex(), 0, 0);
    list.append(Diary{});
    endInsertRows();
    logD() << "dummy populated" << QTime::currentTime();
    qApp->processEvents(QEventLoop::ExcludeUserInputEvents, 150);
    return {};
}

QVector<int> DiaryModel::populate() {
    QTime t;
    t.start();

    if (!list.isEmpty())
        clear();
    int rest = diaryBookSize();
    if (rest == 0)
        return {};
    auto tags = dbDiaryTags();
    auto formats = dbDiaryFormats();
    QMap<int, QPair<QDate,int>> yearFirsts;  // year -> (date, row)

    bool firstChunk = true;
    QString qs = "SELECT * FROM Nikki";
    auto sortBy = settings->value("listSortBy").toString();
    bool reverse = settings->value("listReverse").toBool();
    qs += QString(" ORDER BY ") + ((sortBy == "length") ? "LENGTH(text)" : sortBy);
    if (reverse)
        qs += " DESC";
    QSqlQuery q(qs);
    q.exec();

    while (rest > 0) {
        int count = (firstChunk) ? qMin(16, rest) : rest;
        beginInsertRows(QModelIndex(), 0, count-1);
        while (q.next()) {
            int id = q.value(0).toInt();
            auto text = q.value(2).toString();
            auto title = q.value(3).toString();
            auto dt = QDateTime::fromString(q.value(1).toString(), DB_DATETIME_FMT);

            // save year firsts
            auto date = dt.date();
            auto yearFirstDate = yearFirsts[date.year()].first;
            if (yearFirstDate.isNull())
                yearFirstDate = QDate(9999, 1, 1);
            if (date < yearFirstDate)
                yearFirsts[date.year()] = qMakePair(date, list.size());

            list.append({id, dt, text, title, tags[id], formats[id]});
        }
        endInsertRows();
        if (firstChunk) {
            qApp->processEvents(QEventLoop::ExcludeUserInputEvents);
            firstChunk = false;
        }
        rest -= count;
    }

    QVector<int> ret;
    for (auto &i : yearFirsts)  // already sorted
        ret.append(i.second);

    qDebug("populate took %d ms, %d diaries", t.elapsed(), list.size());
    return ret;
}

void DiaryModel::changeTagName(const QString &from, const QString &to) {
    // dirty way
    for (int row : range(list.count())) {
        int idx = list[row].tags.indexOf(from);
        if (idx != -1)
            list[row].tags[idx] = to;
        auto mIdx = index(row);
        emit dataChanged(mIdx, mIdx);
    }
    execute("UPDATE Tags SET name=? WHERE name=?", {to, from});
}

void DiaryModel::clear() {
    beginResetModel();
    list.clear();
    endResetModel();
}
