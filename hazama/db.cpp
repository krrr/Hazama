#include "db.h"
#include "globals.h"
#include <QMessageBox>
#include <QThread>
#include <QDir>


static QSqlDatabase db;


bool initDb() {
    QSqlQuery q;
    QString path = QDir(dataDir).filePath(settings->value("dbPath").toString());
    db = QSqlDatabase::addDatabase("QSQLITE");
    db.setDatabaseName(path);

    db.setConnectOptions("QSQLITE_BUSY_TIMEOUT=0");
    if (!db.open())
        goto error;
    logI() << "Diary Book loaded:" << path;

    q = QSqlQuery();  // need new one since db changed
    q.exec("PRAGMA foreign_keys = ON");
    q.exec("PRAGMA locking_mode = EXCLUSIVE");  // prevent other instance from visiting one database
    q.exec("PRAGMA application_id = 3442356");  // used for file type determination
    // q.exec("PRAGMA user_version = 1");  uncomment once schema is changed

    // schema
    if (!q.exec("CREATE TABLE IF NOT EXISTS Tags"
                "(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)"))
        goto error;
    q.exec("CREATE TABLE IF NOT EXISTS Nikki"
           "(id INTEGER PRIMARY KEY, datetime TEXT NOT NULL,"
           "text TEXT NOT NULL, title TEXT NOT NULL)");
    q.exec("CREATE TABLE IF NOT EXISTS Nikki_Tags"
           "(nikkiid INTEGER NOT NULL REFERENCES Nikki(id) ON DELETE CASCADE,"
           "tagid INTEGER NOT NULL, PRIMARY KEY(nikkiid, tagid))");
    q.exec("CREATE TABLE IF NOT EXISTS TextFormat"
           "(nikkiid INTEGER NOT NULL REFERENCES Nikki(id) ON DELETE CASCADE,"
           "start INTEGER NOT NULL, length INTEGER NOT NULL, type INTEGER NOT NULL)");

    return true;

error:
    auto err = (q.lastError().type() == QSqlError::NoError) ? db.lastError() : q.lastError();
    logE() << "database error:" << err.text();
    if (err.databaseText() == "database is locked")
        QMessageBox::critical(nullptr, qApp->translate("Errors", "Multiple access error"),
                qApp->translate("Errors", "This diary book is already open."));

    else
        QMessageBox::critical(nullptr, qApp->translate("Errors", "Diary book error"),
                qApp->translate("Errors", "Can't access %1\nDetail: %2").
                arg(settings->value("dbPath").toString()).arg(err.databaseText()));
    return false;
}

int diaryBookSize() {
    QSqlQuery q("SELECT COUNT(*) FROM Nikki");
    q.exec(); q.first();
    return q.value(0).toInt();
}

QString getSqliteVersion() {
    QSqlQuery q("SELECT sqlite_version()");
    q.exec(); q.first();
    return q.value(0).toString();
}

QSqlDatabase *database() {
    Q_ASSERT(QThread::currentThread() == qApp->thread());
    return &db;
}
