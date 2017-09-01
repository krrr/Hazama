#pragma once
#include <QTextDocument>
#include <QColor>
#include <QAbstractTextDocumentLayout>
#include "diarymodel.h"
#include "customobjects/formattermixin.h"

#define NTextDocBase FormatterMixin<NTextDocument, QTextDocument>

class NTextDocument : public NTextDocBase {
public:
    NTextDocument(QObject *parent=nullptr);
    void setText(const QString &text);
    void setTextFormats(const QVector<Diary::TextFormat> &formats);
    QVector<Diary::TextFormat> getTextFormats();
    void drawContentsColor(QPainter *painter, QRect rect, QColor color);
    void drawContentsPalette(QPainter *painter, QRect rect, QPalette palette);

private:
    QTextCursor cursor;
    inline void draw(QPainter *p, QRect rect, QAbstractTextDocumentLayout::PaintContext ctx);
    friend class NTextDocBase;
    inline QTextCursor textCursor();
};
