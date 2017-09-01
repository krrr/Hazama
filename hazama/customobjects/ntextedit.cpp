#include "ntextedit.h"
#include "globals.h"
#include <QIcon>
#include <QAction>
#include <QMimeData>
#include <QMenu>
#include <QTextBlock>
#include "customobjects/ntextdocument.h"

const QTextFormat::Property NTextEdit::fmtAct2charFmt[] = {
            QTextFormat::BackgroundBrush, QTextFormat::FontWeight,
            QTextFormat::FontStrikeOut, QTextFormat::TextUnderlineStyle,
            QTextFormat::FontItalic};  // keep order with fmtActs

NTextEdit::NTextEdit(QWidget *parent) : NTextEditBase(parent) {
    setDocument(new NTextDocument(this));

    auto lang = QLocale().language();
    if (lang == QLocale::Chinese || lang == QLocale::Japanese)
        indent.fill(QChar(0x3000), 2);
    else
        indent.fill(' ', 4);

    // remove highlight color's alpha to avoid alpha loss in copy&paste.
    // NTextDocument should use this color too.
    QColor hl=highLightColor, bg=palette().base().color();
    auto fac = hl.alpha() / 255.0;
    highLightColor = QColor(std::round(hl.red()*fac + bg.red()*(1-fac)),
                            std::round(hl.green()*fac + bg.green()*(1-fac)),
                            std::round(hl.blue()*fac + bg.blue()*(1-fac)));

    fmtMenu = new QMenu(tr("Format"), this);
    highLightAct = new QAction(makeQIcon(":/menu/highlight.png"), tr("Highlight"), fmtMenu);
    highLightAct->setShortcut(QKeySequence("Ctrl+H"));
    connect(highLightAct, &QAction::triggered, this, [&](){ setHighLight(highLightAct->isChecked()); });
    /////////
    boldAct = new QAction(makeQIcon(":/menu/bold.png"), tr("Bold"), fmtMenu);
    boldAct->setShortcut(QKeySequence::Bold);
    connect(boldAct, &QAction::triggered, this, [&](){ setBold(boldAct->isChecked()); });
    /////////
    strikeOutAct = new QAction(makeQIcon(":/menu/strikeout.png"), tr("Strike out"), fmtMenu);
    strikeOutAct->setShortcut(QKeySequence("Ctrl+T"));
    connect(strikeOutAct, &QAction::triggered, this, [&](){ setStrikeOut(strikeOutAct->isChecked()); });
    /////////
    underlineAct = new QAction(makeQIcon(":/menu/underline.png"), tr("Underline"), fmtMenu);
    underlineAct->setShortcut(QKeySequence::Underline);
    connect(underlineAct, &QAction::triggered, this, [&](){ setUnderline(underlineAct->isChecked()); });
    /////////
    italicAct = new QAction(makeQIcon(":/menu/italic.png"), tr("Italic"), fmtMenu);
    italicAct->setShortcut(QKeySequence::Italic);
    connect(italicAct, &QAction::triggered, this, [&](){ setItalic(italicAct->isChecked()); });
    /////////
    clearAct = new QAction(tr("Clear format"), fmtMenu);
    clearAct->setShortcut(QKeySequence("Ctrl+D"));
    connect(clearAct, &QAction::triggered, this, [&](){ textCursor().setCharFormat({}); });
    addAction(clearAct);

    fmtActs = {highLightAct, boldAct, strikeOutAct, underlineAct, italicAct};
    addActions(fmtActs);
    for (auto i : fmtActs)
        i->setCheckable(true);
    fmtMenu->addActions(fmtActs);
    fmtMenu->addSeparator();
    fmtMenu->addAction(clearAct);
}

void NTextEdit::contextMenuEvent(QContextMenuEvent *e) {
    auto menu = createStandardContextMenu();
    setStdEditMenuIcons(menu);

    if (!isReadOnly()) {
        if (textCursor().hasSelection()) {
            setFmtStates();
            fmtMenu->setEnabled(true);
        } else
            fmtMenu->setEnabled(false);
        auto before = menu->actions()[2];
        menu->insertSeparator(before);
        menu->insertMenu(before, fmtMenu);
    }
    menu->exec(e->globalPos());
    menu->deleteLater();
}

void NTextEdit::keyPressEvent(QKeyEvent *e) {
    if (isReadOnly())
        return NTextEditBase::keyPressEvent(e);

    switch (e->key()) {
    case Qt::Key_H: case Qt::Key_U: case Qt::Key_B: case Qt::Key_T: case Qt::Key_I:
        // set actions before calling format methods
        setFmtStates();
        return NTextEditBase::keyPressEvent(e);
    case Qt::Key_Tab:
        // will not receive event if tabChangesFocus is True
        return textCursor().insertText(indent);
    case Qt::Key_Return:  // auto-indent support
        if (autoIndent) {
            auto para = textCursor().block().text();
            QChar space = para[0];
            if (para.length() > 0 && contains(autoIndentSpaceTypes, space)) {
                int spaceCount = 0;
                for (auto i : para) {
                    if (i != space) break;
                    spaceCount += 1;
                }
                NTextEditBase::keyPressEvent(e);
                textCursor().insertText(QString(spaceCount, space));
                return;
            }
        }  // else fall through
    default:
        return NTextEditBase::keyPressEvent(e);
    }
}

void NTextEdit::setRichText(const QString &text, const QVector<Diary::TextFormat> &formats) {
    auto doc = static_cast<NTextDocument*>(document());
    doc->setText(text);
    doc->setTextFormats(formats);
    doc->getTextFormats();
}

QPair<QString, QVector<Diary::TextFormat>> NTextEdit::getRichText() {
    auto doc = static_cast<NTextDocument*>(document());
    return { doc->toPlainText(), doc->getTextFormats() };
}

// Disable some unsupported types
void NTextEdit::insertFromMimeData(const QMimeData *source) {
    auto h = source->html();
    insertHtml((h.isEmpty()) ? source->text() : h);
}

// Check formats in current selection and check or uncheck actions
void NTextEdit::setFmtStates() {
    auto cur = textCursor();
    int start=cur.anchor(), end=cur.position();
    if (start > end)
        std::swap(start, end);
    QVector<bool> results(5);
    std::fill(results.begin(), results.end(), true);
    for (int pos : range(end, start, -1)) {
        cur.setPosition(pos);
        auto charFmt = cur.charFormat();
        for (int i : range(results.size()))
            if (results[i] && !charFmt.hasProperty(fmtAct2charFmt[i]))
                results[i] = false;

        if (!std::any_of(results.begin(), results.end(), is_true))
            break;
    }
    for (int i : range(results.size()))
        fmtActs[i]->setChecked(results[i]);
}
