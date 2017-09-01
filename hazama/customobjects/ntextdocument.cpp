#include "ntextdocument.h"
#include <QPainter>
#include <QTextBlock>


NTextDocument::NTextDocument(QObject *parent) : NTextDocBase(parent) {
}

void NTextDocument::setText(const QString &text) {
    setPlainText(text);

    clearUndoRedoStacks();
    setModified(false);
}

void NTextDocument::setTextFormats(const QVector<Diary::TextFormat> &formats) {
    cursor = QTextCursor(this);
    bool m = isModified();
    for (auto i : formats) {
        cursor.setPosition(i.index);
        cursor.setPosition(i.index+i.length, QTextCursor::KeepAnchor);
        switch (i.type) {
        case Diary::TextFormat::Type::HighLight:
            setHighLight(true);
            break;
        case Diary::TextFormat::Type::Bold:
            setBold(true);
            break;
        case Diary::TextFormat::Type::StrikeOut:
            setStrikeOut(true);
            break;
        case Diary::TextFormat::Type::Underline:
            setUnderline(true);
            break;
        case Diary::TextFormat::Type::Italic:
            setItalic(true);
            break;
        }
    }
    setModified(m);
    cursor = QTextCursor();  // set to null
}

QVector<Diary::TextFormat> NTextDocument::getTextFormats() {
    static const QPair<Diary::TextFormat::Type, QTextFormat::Property> fmt2qFmt[] = {
        qMakePair(Diary::TextFormat::Type::Bold, QTextFormat::FontWeight),
        qMakePair(Diary::TextFormat::Type::HighLight, QTextFormat::BackgroundBrush),
        qMakePair(Diary::TextFormat::Type::Italic, QTextFormat::FontItalic),
        qMakePair(Diary::TextFormat::Type::StrikeOut, QTextFormat::FontStrikeOut),
        qMakePair(Diary::TextFormat::Type::Underline, QTextFormat::TextUnderlineStyle),
    };

    QVector<Diary::TextFormat> ret;
    for (auto block=begin(); block!=end(); block=block.next())  // no way to use C++ 11 for
        for (auto i=block.begin(); !i.atEnd(); i++) {
            auto frag = i.fragment();
            auto charFmt = frag.charFormat();
            for (auto i : fmt2qFmt)
                if (charFmt.hasProperty(i.second))
                    ret.append({frag.position(), frag.length(), i.first});
        }
    return ret;
}

QTextCursor NTextDocument::textCursor() {
    return cursor;
}

/* Using given color to draw contents */
void NTextDocument::drawContentsColor(QPainter *painter, QRect rect, QColor color) {
    QAbstractTextDocumentLayout::PaintContext ctx;
    ctx.palette.setColor(QPalette::Text, color);
    draw(painter, rect, ctx);
}

/* Using given palette to draw contents instead of app default */
void NTextDocument::drawContentsPalette(QPainter *painter, QRect rect, QPalette palette) {
    QAbstractTextDocumentLayout::PaintContext ctx;
    ctx.palette = palette;
    draw(painter, rect, ctx);
}

void NTextDocument::draw(QPainter *painter, QRect rect, QAbstractTextDocumentLayout::PaintContext ctx) {
    painter->save();
    if (rect.isValid()) {
        painter->setClipRect(rect);
        ctx.clip = rect;
    }
    documentLayout()->draw(painter, ctx);
    painter->restore();
}
