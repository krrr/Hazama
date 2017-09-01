#include "globals.h"
#include <QMessageBox>
#include <QFile>
#include <QIcon>
#include <QMenu>
#include <QStyle>
#include <QDir>
#include <QProcessEnvironment>
#include <QDesktopWidget>
#include <QSysInfo>
#include <QRegularExpression>
#include "db.h"


//// global variables
QLocale locale;
// datetimeFmt may not contain time part (by default)
QString timeFmt, dateFmt, datetimeFmt, fullDatetimeFmt;
Fonts fonts;
double scaleRatio = -1;
QString dataDir;
QSettings *settings = nullptr;

const QStringList TRANSLATION {"en", "zh_CN", "ja_JP"};
const QStringList TRANS_DISPLAY_NAMES {"English", "简体中文", "日本語"};

OsInfo::OsInfo() {
    isWin = isWinVistaOrLater = isWin7 = isWin7OrLater = isWin8 = isWin8OrLater = isWin10 = false;
#ifdef Q_OS_WIN
    isWin = true;
    auto verStrs = QSysInfo::kernelVersion().split(".");
    auto ver = qMakePair(verStrs[0].toInt(), (verStrs.size()>1) ? verStrs[1].toInt() : 0);
    isWinVistaOrLater = ver > qMakePair(6, 0);
    isWin7 = ver == qMakePair(6, 1);
    isWin7OrLater = ver > qMakePair(6, 1);
    isWin8 = ver == qMakePair(6, 2);
    isWin8OrLater = ver > qMakePair(6, 2);
    isWin10 = ver == qMakePair(10, 0);
#endif
}

const OsInfo osInfo;


static const QPair<const char*, QVariant> defaultSettings[] = {
    {"iniVersion", 1},
    {"debug", false},
    {"backup", true},
    {"dbPath", "nikkichou.db"},
    {"tagListCount", true},
    {"previewLines", 4},
    {"listSortBy", "datetime"},
    {"listReverse", true},
    {"listAnnotated", true},
    {"tagListVisible", false},
    {"listAnnotated", true},
    // some value require runtime info, such as extendTitleBarBg | theme
    {"Editor/autoIndent", true},
    {"Editor/titleFocus", false},
    {"Editor/autoReadonly", true},
    {"Editor/tabIndent", true},
    {"Font/enhanceRender", false},
    {"Update/autoCheck", true},
    {"Update/newestIgnoredVer", "0.0.0"},
    {"Update/needClean", false},
    {"ThemeColorful/colorScheme", "green"},
};

/* Localize datetime in database format. */
QString datetimeTrans(QString s, bool stripTime) {
    return datetimeTrans(QDateTime::fromString(s, DB_DATETIME_FMT), stripTime);
}

QString datetimeTrans(QDateTime dt, bool stripTime) {
    return locale.toString(dt, (stripTime) ? dateFmt : datetimeFmt);
}

QString readRcTextFile(const QString &path) {
    /* Read whole text file from qt resources system. */
    Q_ASSERT(path.startsWith(":/"));
    QFile f(path);
    if (!f.open(QFile::ReadOnly | QFile::Text))
        return "";
    return QString(f.readAll());
}


QByteArray readRcFile(const QString &path) {
    /* Read whole binary file from qt resources system. */
    Q_ASSERT(path.startsWith(":/"));
    QFile f(path);
    if (!f.open(QFile::ReadOnly))
        return QByteArray();
    return f.readAll();
}

void setTranslationLocale() {
    auto sysLocale = QLocale::system();
    auto lang = settings->value("lang").toString();

    if (lang.isEmpty()) {
        if (TRANSLATION.contains(sysLocale.name()))
            settings->setValue("lang", sysLocale.name());
        else
            settings->setValue("lang", "en");
    }

    if (lang == "en" || sysLocale.name() == lang)  // use system's locale
        // lang=='en' because user is likely to use English if his lang is not supported
        locale = sysLocale;
    else  // override system's locale
        locale = QLocale(lang);
    QLocale::setDefault(locale);

    logI() << "set translation:" << lang;
    static QTranslator trans;  // must hold
    static QTranslator transQt;
    if (lang != "en") {
        static auto dat1 = readRcFile(":/trans_qt.qm");  // must hold
        if (!dat1.isEmpty())
            trans.load(reinterpret_cast<const uchar*>(dat1.constData()), dat1.length());
        else
            logE() << "failed to load translation for locale:" << locale.name();
        qApp->installTranslator(&trans);

        static auto dat2 = readRcFile(":/trans_qt.qm");
        if (!dat2.isEmpty())
            transQt.load(reinterpret_cast<const uchar*>(dat2.constData()), dat2.length());
        else
            transQt.load("qt_"+locale.name(), QLibraryInfo::location(QLibraryInfo::TranslationsPath));
        qApp->installTranslator(&transQt);
    }

    timeFmt = settings->value("timeFmt").toString();
    dateFmt = settings->value("dateFmt", locale.dateFormat()).toString();
    datetimeFmt = (timeFmt.isEmpty()) ? dateFmt : dateFmt+' '+timeFmt;
    // use hh:mm because locale.timeFormat will include seconds
    fullDatetimeFmt = dateFmt + ' ' + ((timeFmt.isEmpty()) ? "hh:mm" : timeFmt);
}

/* A Shortcut to construct a QIcon which has multiple images
 * (xx.png & xx-big.png & xx-mega.png)." */
QIcon makeQIcon(QString filename, bool scaled2x) {
    Q_ASSERT(filename.contains(QChar('.')));
    auto parts = rsplit(filename, ".");
    auto ico = QIcon(filename);
    ico.addFile(parts[0] + "-big." + parts[1]); // fails silently when file not exist
    if (scaled2x && scaleRatio > 1.5) {
        QPixmap origin;
        ico.addPixmap(origin.scaled(origin.size() * 2));
    } else
        ico.addFile(parts[0] + "-mega." + parts[1]);

    return ico;
}

QIcon makeQIcon(QStringList filenames, bool) {
    QIcon ret;
    for (auto i : filenames)
        ret.addFile(i);
    return ret;
}

/* Add system theme icons to QLineEdit and QTextEdit context-menu. */
void setStdEditMenuIcons(QMenu *menu) {
#ifdef Q_OS_WIN
    Q_UNUSED(menu)
#else
    auto acts = menu->actions();
    if (acts.size() < 9)
        return;
    // undo, redo, __, cut, copy, paste, delete, __, sel, *__
    acts[0]->setIcon(QIcon::fromTheme("edit-undo"));
    acts[1]->setIcon(QIcon::fromTheme("edit-redo"));
    acts[3]->setIcon(QIcon::fromTheme("edit-cut"));
    acts[4]->setIcon(QIcon::fromTheme("edit-copy"));
    acts[5]->setIcon(QIcon::fromTheme("edit-paste"));
    acts[6]->setIcon(QIcon::fromTheme("edit-delete"));
    acts[8]->setIcon(QIcon::fromTheme("edit-select-all"));
#endif
}

QString saveWidgetGeo(const QWidget *w) {
    return QString("%1,%2").arg(QString(w->saveGeometry().toHex())).arg(scaleRatio);
}

/* Simply resize current size according to DPI. Should be called after setupUi. */
void fixWidgetSizeHiDpi(QWidget *w) {
    if (scaleRatio > 1) {
        w->resize(w->size() * scaleRatio);
        w->setMinimumSize(w->minimumSize() * scaleRatio);  // prevent over sizing after resize
    }
}

void restoreWidgetGeo(QWidget *w, const QString &s) {
    if (s.isEmpty() || !s.contains(','))
        return fixWidgetSizeHiDpi(w);

    auto parts = s.split(',');
    auto oldRatio=parts[1].toDouble();
    bool success = w->restoreGeometry(QByteArray::fromHex(parts[0].toUtf8()));
    auto ratio = scaleRatio / oldRatio;
    if (success && qAbs(ratio - 1) > 0.01) {
        w->move(w->pos() * ratio);
        w->resize(w->size() * ratio);
    }
}

void refreshStyle(QWidget *w) {
    w->style()->unpolish(w);
    w->style()->polish(w);
}

QString getDataDir() {
    if (qApp->arguments().contains("-portable") ||
            QFile::exists(qApp->applicationDirPath() + "/config.ini"))
        return qApp->applicationDirPath();

    // non portable mode
#ifdef Q_OS_WIN
    auto env = QProcessEnvironment::systemEnvironment();
    auto path = env.value("APPDATA") + "/Hazama";
#else
    auto path = QDir::homePath() + "/.config/Hazama" + "Hazama";
#endif
    QDir::current().mkpath(path);
    return path;
}

bool initSettings() {
    Q_ASSERT(!dataDir.isEmpty());
    auto iniPath = dataDir + "/config.ini";
    settings = new QSettings(iniPath, QSettings::IniFormat, qApp);
    if (settings->status() == QSettings::AccessError) {
        qCritical("failed to open settings");
        QMessageBox::critical(nullptr, qApp->translate("Errors", "Can't open config file"),
                              qApp->translate("Errors", "Can't open %1").arg(iniPath));
        return false;
    } else if (settings->status() == QSettings::FormatError) {
        qCritical("ill-formed config file");
        QMessageBox::critical(nullptr, qApp->translate("Errors", "Config file corrupted"),
                              qApp->translate("Errors", "%1 is corrupted, please delete or fix it.").arg(iniPath));
        return false;
    }

    // update old version
    int iniVer = settings->value("iniVersion", 0).toInt();
    bool emptyIni = iniVer == 0 && settings->allKeys().length() == 0;
    if (!emptyIni && iniVer == 0) {
        qInfo() << "upgrade config.ini from ver 0 to 1";
        // 0 is made by python stdlib, and it doesn't escape backslash
        QFile f(iniPath);
        f.open(QIODevice::ReadWrite | QIODevice::Text);
        auto ini = f.readAll();
        delete settings;
        ini.replace("\\", "\\\\");
        ini.replace("[Main]", "[General]");
        f.seek(0);
        f.write(ini);
        f.close();

        settings = new QSettings(iniPath, QSettings::IniFormat, qApp);
        // QSettings require strings being quoted
        settings->remove("Main/windowGeo");
        settings->remove("Editor/windowGeo");
        for (auto i : {"text", "title", "datetime", "default"})
            settings->remove(QString("Font/") + i);
        iniVer = 1;
        settings->setValue("iniVersion", 1);
    }
    // insert ver1 update code here, in the future...

    // set default values. some values have no defaults, such as windowGeo and tagListWidth
    for (auto &i : defaultSettings)
        if (!settings->contains(i.first))
            settings->setValue(i.first, i.second);

    // prevent QSettings from sync to disk frequently
    class Filter : public QObject {
        using QObject::QObject;
        bool eventFilter(QObject *obj, QEvent *e) {
            if (e->type() == QEvent::UpdateRequest) {
                return true;
            } else
                return QObject::eventFilter(obj, e);
        }
    };
    auto f = new Filter(qApp);
    settings->installEventFilter(f);
    return true;
}

/* support custom device independent pixel (dip), like px in CSS
 * 1dip @96DPI == 1px
 * 1dip @ 144DPI == 1px  (for hair lines) */
void setStyleSheetPatched(const QString &ss) {
    static QRegularExpression re("\\b(\\d+)dip");
    Q_ASSERT(scaleRatio != -1);

    qApp->setProperty("originStyleSheet", ss);
    auto i = re.globalMatch(ss);
    QString subed;
    int preEnd=0;
    while (i.hasNext()) {
        auto match = i.next();
        subed.append(ss.mid(preEnd, match.capturedStart()-preEnd));
        subed.append(QString::number(myRound(match.captured(1).toInt() * scaleRatio)) + "px");
        preEnd = match.capturedEnd();
    }
    subed.append(ss.mid(preEnd, ss.length()-preEnd));
    qApp->setStyleSheet(subed);
}

/* If -stylesheet not in sys.argv, append custom.qss(if any) to default one and
   load it. Otherwise load the one in sys.argv */
void loadStyleSheet() {
    if (qApp->arguments().contains("-stylesheet")) {
        logI() << "override default StyleSheet by command line arg";
        return;
    }

    auto ss = readRcTextFile(":/default.qss");
    // append theme part
    if (settings->value("theme").toString() == "colorful") {
        ss.append(readRcTextFile(":/colorful.qss"));
        auto scheme = settings->value("ThemeColorful/colorScheme").toString();
        if (scheme != "green")
            ss.append(readRcTextFile(QString(":/colorful-%1.qss").arg(scheme)));
    }
    // load custom
    ss.append(CUSTOM_STYLESHEET_DELIMIT);
    auto path = dataDir + "/custom.qss";
    if (QFile::exists(path)) {
        logI() << "load custom StyleSheet";
        QFile f(path);
        ss.append('\n');
        if (f.open(QFile::ReadOnly | QFile::Text))
            ss.append(f.readAll());
    }
    setStyleSheetPatched(ss);
}
