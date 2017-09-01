#include "globals.h"
#include <QLocale>
#include <QFontInfo>


const QMap<QString, QVector<QString>> PREFFERED_FONTS = {  // unlike CSS, if font family name is localized then its English name will be ignored
    {"zh_CN", {"Microsoft YaHei", "微软雅黑",
               "WenQuanYi Micro Hei", "WenQuanYi Zen Hei", "文泉驿正黑",
               "Noto Sans CJK SC", "Source Han Sans CN Normal", "思源黑体"}},
    {"ja_JP", {"Yu Gothic Medium", "游ゴシック Medium", "Meiryo", "メイリオ", "Noto Sans CJK JP"}},
    {"zh_TW", {"Microsjft JhengHei", "微软正黑体", "Noto Sans CJK TC"}},
};


/* Return preferred font according to language and platform."""
 * 1. get sans-serif CJ fonts that looks good on HiDPI
 * 2. fix when app font doesn't match system's, this will cause incorrect lineSpacing (
 * an attempt to use QFontDatabase to auto get right font was failed) */
static QString getPreferredFont() {
    if (osInfo.isWin && scaleRatio==1 && settings->value("theme").toString()=="1px-rect")
        // old theme looks fine with default bitmap fonts only on normal DPI (SimSun)
        return "";

    auto lo=QLocale(), loSys=QLocale::system();
    auto lst = PREFFERED_FONTS[(lo.language()!=loSys.language()) ? lo.name() : loSys.name()];
    if (lst.isEmpty())
        return "";
    QFont f;
    for (auto i : lst) {
        f.setFamily(i);
        if (f.exactMatch())
            return i;
    }
    return "";

}

void Fonts::load() {
    app = qApp->font();
    auto saved = settings->value("Font/app").toString();
    auto preferred = (saved.isEmpty()) ? getPreferredFont() : saved;
    if (!saved.isEmpty())
        app.fromString(saved);
    else if (!preferred.isEmpty())
        app.setFamily(preferred);
    userSet["app"] = !saved.isEmpty();
    logD() << "app font:" << app.family() << QString::number(app.pointSize()) << "pt";
    qApp->setFont(app);

    loadSetting(title, "title");
    loadSetting(datetime, "datetime");
    loadSetting(text, "text");
}

void Fonts::loadSetting(QFont &f, const char *name) {
    f.setHintingPreference(QFont::PreferNoHinting);
    auto saved = settings->value(QString("Font/") + name).toString();
    if (!saved.isEmpty()) {
        f.fromString(saved);
        userSet[name] = true;
    } else {
        // document says f.family() == '' will use app font, but it not work on Linux
        // userSet attr is for this
        f = qApp->font();
        userSet[name] = false;
    }
    // exactMatch may be broken with fromString
}

