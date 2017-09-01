#pragma once
#include <QTextEdit>
#include "diarymodel.h"
#include "customobjects/formattermixin.h"

#define NTextEditBase FormatterMixin<NTextEdit, QTextEdit>

class NTextEdit : public NTextEditBase {
public:
    static constexpr QChar autoIndentSpaceTypes[] = {' ', 0x3000};  // full width space U+3000

    NTextEdit(QWidget *parent=nullptr);
    void setRichText(const QString &text, const QVector<Diary::TextFormat> &formats);
    QPair<QString, QVector<Diary::TextFormat>> getRichText();
    void setAutoIndent(bool to) { autoIndent = to; }

protected:
    void insertFromMimeData(const QMimeData *source);
    void contextMenuEvent(QContextMenuEvent *e);
    void keyPressEvent(QKeyEvent *e);

private:
    bool autoIndent = true;
    QAction *highLightAct, *boldAct, *strikeOutAct, *underlineAct, *italicAct, *clearAct;
    QList<QAction*> fmtActs;
    QString indent;  // used by tab indent shortcut
    static const QTextFormat::Property fmtAct2charFmt[];
    QMenu *fmtMenu;

    void setFmtStates();
};
