#pragma once
#include <QDateTime>
#include <QModelIndex>
#include <QAbstractListModel>


struct Diary {
    struct TextFormat {
        enum class Type {
            Bold = 1,
            HighLight,
            Italic,
            StrikeOut,
            Underline,
        };

        int index;
        int length;
        Type type;
    };

    int id;
    QDateTime datetime;
    QString text;
    QString title;
    QStringList tags;
    QVector<TextFormat> formats;
    // don't worry about copy because of copy-on-write
};

Q_DECLARE_METATYPE(Diary)


class DiaryModel : public QAbstractListModel {
public:
    static DiaryModel *instance;

    DiaryModel(QObject *parent=nullptr);
    ~DiaryModel();
    int rowCount(const QModelIndex &parent) const;
    QVariant data(const QModelIndex &index, int role=Qt::DisplayRole) const;
    bool setData(const QModelIndex &index, const QVariant &value, int role=Qt::EditRole);
    int saveDiary(const Diary &diary, bool ignoreTags=false, bool batch=false);
    void deleteDiary(int row);
    bool insertRows(int row, int count, const QModelIndex &parent=QModelIndex());
    bool removeRows(int row, int count, const QModelIndex &parent=QModelIndex());
    QVector<int> populateDummy();  // for debug
    QVector<int> populate();  // return the row of first diary of every year, sorted
    void changeTagName(const QString &from, const QString &to);
    void clear();

private:
    QVector<Diary> list;

    int getRowById(int id);
};
