#pragma once
#include <QApplication>
#include <QDebug>
#include <QSettings>
#include <QFont>
#include <QFontMetrics>
#include "cppassist.h"

#define CUSTOM_STYLESHEET_DELIMIT "/**** BEGIN CUSTOM STYLESHEET ****/"
#define APP_VER "1.1.0"

#define ilist std::initializer_list

class QMenu;

/* Manage all fonts used in application */
class Fonts {
public:
    QFont title, datetime, text, app;

    void load();

private:
    QMap<QString, bool> userSet;

    void loadSetting(QFont &f, const char *name);
};

/* Share global variables (they are set in main.cpp, and almost read-only), and
 * constants  */
extern Fonts fonts;
extern double scaleRatio;
extern QString dataDir;
extern QSettings *settings;
extern QString timeFmt, dateFmt, datetimeFmt, fullDatetimeFmt;

struct OsInfo {
    bool isWin, isWinVistaOrLater, isWin7, isWin7OrLater, isWin8, isWin8OrLater, isWin10;
    OsInfo();
};
extern const OsInfo osInfo;

void setStdEditMenuIcons(QMenu *menu);
QString datetimeTrans(QString s, bool stripTime=true);
QString datetimeTrans(QDateTime dt, bool stripTime=true);
QIcon makeQIcon(QString filename, bool scaled2x=false);
QIcon makeQIcon(QStringList filenames, bool scaled2x=false);
QString saveWidgetGeo(const QWidget *w);
void restoreWidgetGeo(QWidget *w, const QString &s);
void refreshStyle(QWidget *w);
void fixWidgetSizeHiDpi(QWidget *w);
QByteArray readRcFile(const QString &path);
QString readRcTextFile(const QString &path);
void setStyleSheetPatched(const QString &ss);
QString getDataDir();
bool initSettings();
void loadStyleSheet();
void setTranslationLocale();


/* inline functions */
inline QDebug logD() { return qDebug().noquote(); }
inline QDebug logI() { return qInfo().noquote(); }
inline QDebug logE() { return qCritical().noquote(); }

// get correct metrics on HiDPI screen
inline QFontMetrics fontMetric(const QFont &f) { return QFontMetrics(f, nullptr); }
