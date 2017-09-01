#include "editor.h"
#include "QShortcut"
#include "globals.h"
#include "customobjects/nshadoweffect.h"
#include "customobjects/datetimedialog.h"

#ifdef Q_OS_WIN
#include <windows.h>
#include <windowsx.h>
#include <QtWinExtras/QtWin>
#endif


Editor::Editor(QWidget *parent) : QFrame(parent) {
    setupUi(this);
    lockBtn->hide();
    restoreWidgetGeo(this, settings->value("Editor/windowGeo").toString());

    titleEditor->setFont(fonts.title);
    connect(titleEditor, &QLineEdit::returnPressed, [&](){
        if (!readOnly)
            textEditor->setFocus();
    });
    textEditor->setFont(fonts.text);
    textEditor->setAutoIndent(settings->value("Editor/autoIndent").toBool());
    textEditor->setTabChangesFocus(!settings->value("Editor/tabIndent").toBool());

    tagEditor->setTextMargins(QMargins(2, 0, 2, 0));
    //tagEditor->setCompleter(TagCompleter(list(db.get_tags()), self.tagEditor));
    connect(tagEditor, &QLineEdit::returnPressed, [&](){
        if (!readOnly)
            box->button(QDialogButtonBox::Save)->setFocus();
    });
    // tagEditor.isModified() will be reset by completer. Use this instead.
    connect(tagEditor, &QLineEdit::textEdited, [&](){ tagModified = true; });

    dtBtn->setFont(fonts.datetime);
    int sz = qMax(QFontMetrics(fonts.datetime).ascent(), 12);
    dtBtn->setIconSize(QSize(sz, sz));
    lockBtn->setIconSize(QSize(sz, sz));
    connect(lockBtn, &QPushButton::clicked, [&](){ setReadOnly(false); });

    if (osInfo.isWin10 && settings->value("extendTitleBarBg").toBool())
        bottomArea->setProperty("bgType", "win10");

    //// setup shortcuts
    // seems PySide has problem with QKeySequence.StandardKeys
    closeSaveSc = new QShortcut(QKeySequence::Save, this);
    connect(closeSaveSc, &QShortcut::activated, this, &Editor::close);
    closeNoSaveSc = new QShortcut(QKeySequence("Ctrl+W"), this);
    connect(closeNoSaveSc, &QShortcut::activated, this, &Editor::closeNoSave);
    quickCloseSc = new QShortcut(QKeySequence("Esc"), this);
    connect(quickCloseSc, &QShortcut::activated, this, &Editor::closeNoSave);
    // Ctrl+Shift+Backtab doesn't work
    preSc = new QShortcut(QKeySequence("Ctrl+Shift+Tab"), this);
    quickPreSc = new QShortcut(QKeySequence("Left"), this);
    nextSc = new QShortcut(QKeySequence("Ctrl+Tab"), this);
    quickNextSc = new QShortcut(QKeySequence("Right"), this);
}

void Editor::showEvent(QShowEvent *e) {
    Q_UNUSED(e)
    applyExtendTitleBarBg();
    if (settings->value("Editor/titleFocus").toBool())
        titleEditor->setCursorPosition(0);
    else {
        textEditor->setFocus();
        textEditor->moveCursor(QTextCursor::Start);
    }
}

void Editor::closeEvent(QCloseEvent *e) {
    Q_UNUSED(e)
    settings->setValue("Editor/windowGeo", saveWidgetGeo(this));
    emit closed(id, (noSave) ? false : isModified());
}

#ifdef Q_OS_WIN
bool Editor::nativeEvent(const QByteArray &eventType, void *message, long *result) {
    if (eventType != QByteArrayLiteral("windows_generic_MSG"))
        return false;
    auto msg = static_cast<MSG*>(message);
    if (msg->message == WM_NCHITTEST) {
        auto globalPos = QPoint(GET_X_LPARAM(msg->lParam), GET_Y_LPARAM(msg->lParam));
        auto pos = mapFromGlobal(globalPos);
        auto widget = childAt(pos);
        if (widget == bottomArea) {
            *result = HTCAPTION;
            return true;
        }
    }
    return false;
}
#endif

// Handle mouse back/forward button
void Editor::mousePressEvent(QMouseEvent *event) {
    if (event->button() == Qt::XButton1) {  // back
        emit preSc->activated();
        event->accept();
    } else if (event->button() == Qt::XButton2) {  // forward
        emit nextSc->activated();
        event->accept();
    } else
        QFrame::mousePressEvent(event);
}

void Editor::applyExtendTitleBarBg() {
    if (settings->value("extendTitleBarBg").toBool()) {
#ifdef Q_OS_WIN
        if (!QtWin::isCompositionEnabled())
            return;
        QtWin::extendFrameIntoClientArea(this, 0, 0, 0, bottomArea->height());
        setAttribute(Qt::WA_TranslucentBackground);
        // Qt5 only hack, Qt4 doesn't need this
        setAttribute(Qt::WA_NoSystemBackground, false);  // it's set by WA_TranslucentBackground
        // force background of MainWindow to be cleared before its contents being painted
        QPalette pal = palette();
        pal.setColor(QPalette::Background, Qt::transparent);
        setPalette(pal);
#endif
        for (auto i : {dtBtn, lockBtn}) {
            auto eff = new NShadowEffect((osInfo.isWin7) ? 5 : 3, i);
            eff->setColor(QColor(Qt::white));
            eff->setOffset(0, 0);
            eff->setBlurRadius(((osInfo.isWin7) ? 16 : 8) * scaleRatio);
            i->setGraphicsEffect(eff);
        }
    } else {
#ifdef Q_OS_WIN
        QtWin::resetExtendedFrame(this);
        setPalette(QApplication::palette(this));  // set palette to default one
#endif
        for (auto i : {dtBtn, lockBtn}) {
            auto eff = i->graphicsEffect();
            if (eff) {
                i->setGraphicsEffect(nullptr);
                delete eff;
            }
        }
    }
}

void Editor::fromDiary(const Diary &d) {
    timeModified = tagModified = false;
    id = d.id;
    datetime = d.datetime;
    dtBtn->setText((datetime.isNull()) ? "" : datetimeTrans(datetime));
    titleEditor->setText(d.title);
    tagEditor->setText(d.tags.join(" "));
    textEditor->setRichText(d.text, d.formats);
    // if title is empty, use datetime instead. if no datetime (new), use "New Diary"
    auto t = d.title;
    if (t.isEmpty() && !datetime.isNull())
        t = dtBtn->text();
    if (t.isEmpty())
        t = tr("New Diary");
    setWindowTitle(QString("%1 - Hazama").arg(t));

    setReadOnly(settings->value("Editor/autoReadOnly").toBool() &&
                !datetime.isNull() &&
                datetime.daysTo(QDateTime::currentDateTime()) > 3);
}

Diary Editor::toDiary() {
    auto rt = textEditor->getRichText();
    auto tags = tagEditor->text().split(" ", QString::SkipEmptyParts);
    if (tagModified)
        tags.removeDuplicates();
    auto dt = (datetime.isNull()) ? QDateTime::currentDateTime() : datetime;
    return { id, dt, rt.first, titleEditor->text(), tags, rt.second };
}

bool Editor::isModified() {
    return textEditor->document()->isModified() ||
           titleEditor->isModified() || timeModified || tagModified;
}

void Editor::setReadOnly(bool to) {
    readOnly = to;
    titleEditor->setReadOnly(to);
    textEditor->setReadOnly(to);
    tagEditor->setReadOnly(to);
    dtBtn->setCursor((to) ? Qt::ArrowCursor : Qt::PointingHandCursor);
    box->setStandardButtons((to) ? QDialogButtonBox::Close :
                            QDialogButtonBox::Save | QDialogButtonBox::Cancel);
    box->button((to) ? QDialogButtonBox::Close : QDialogButtonBox::Save)->setDefault(true);
    lockBtn->setVisible(to);
    titleEditor->setVisible(!to || !titleEditor->text().isEmpty());
    tagEditor->setVisible(!to || !tagEditor->text().isEmpty());
    for (auto i : {quickCloseSc, quickPreSc, quickNextSc})
        i->setEnabled(to);

#ifdef Q_OS_WIN
    if (settings->value("extendTitleBarBg").toBool())  // height may change
        QtWin::extendFrameIntoClientArea(this, 0, 0, 0, bottomArea->height());
#endif
}

void Editor::editDateTime() {
    if (readOnly)
        return;
    auto dt = (datetime.isNull()) ? QDateTime::currentDateTime() : datetime;
    auto newDt = DateTimeDialog::getDateTime(dt, fullDatetimeFmt, this);
    if (!newDt.isNull() && newDt != dt) {
        datetime = newDt;
        dtBtn->setText(datetimeTrans(newDt));
        timeModified = true;
    }
}
