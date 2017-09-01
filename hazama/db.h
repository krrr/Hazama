#pragma once
#include <QtSql>

#define DB_DATETIME_FMT "yyyy-MM-dd HH:mm"

bool initDb();

int diaryBookSize();

QString getSqliteVersion();

QSqlDatabase *database();
