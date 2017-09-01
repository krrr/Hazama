#include <QTimer>
#include <QLabel>
#include <QMenu>
#include <QPushButton>
#include <QShortcut>
#include <QToolButton>
#include <QDesktopServices>
#include <QPropertyAnimation>
#include <QMessageBox>
#include <QTextLayout>
#include "globals.h"
#include "mainwindow.h"
#include "searchbox.h"
#include "qsseditor.h"
#include "heatmap.h"
#include "diarymodel.h"
#include "customobjects/nshadoweffect.h"

#ifdef Q_OS_WIN
#include <windows.h>
#include <windowsx.h>
#include <QtWinExtras/QtWin>
#endif


MainWindow::MainWindow(QWidget *parent) : QMainWindow(parent) {
    setupUi(this);

    restoreWidgetGeo(this, settings->value("windowGeo").toString());
    setToolBarProperty();  // setup toolbar bg properties; the second stage is in showEvent
    if (scaleRatio > 1) {
        toolBar->setIconSize(QSize(24, 24) * scaleRatio);
        cfgAct->setIcon(makeQIcon(":/toolbar/config.png"));
        creAct->setIcon(makeQIcon(":/toolbar/new.png"));
        delAct->setIcon(makeQIcon(":/toolbar/delete.png"));
        mapAct->setIcon(makeQIcon(":/toolbar/heatmap.png"));
        sorAct->setIcon(makeQIcon(":/toolbar/sort.png"));
        tListAct->setIcon(makeQIcon(":/toolbar/tag-list.png"));
    }
    connect(diaryList, &DiaryList::startLoading, [&]() {
        countLabel->setText(tr("loading..."));
    });
    connect(diaryList, &DiaryList::countChanged, this, &MainWindow::updateCountLabel);
    connect(diaryList->editAct, &QAction::triggered, this, &MainWindow::startEditor);
    connect(diaryList->gotoAct, &QAction::triggered, this, &MainWindow::onDiaryListGoto);
    connect(diaryList->delAct, &QAction::triggered, this, &MainWindow::deleteSelectedDiary);

    // setup tag list
    tagListAni = new QPropertyAnimation(this, "tagListWidth", this);
    tagListAni->setEasingCurve(QEasingCurve(QEasingCurve::OutCubic));
    tagListAni->setDuration(150);
    connect(tagListAni, &QPropertyAnimation::finished, [&](){
        if (tagListAni->endValue().toInt() == 0)
            tagList->hide();
        else
            tagList->setMinimumWidth(75 * scaleRatio);
    });

    if (settings->value("tagListVisible").toBool()) {
        tListAct->setChecked(true);  // will not trigger signal
        toggleTagList(true, false);
    } else
        tagList->hide();  // don't use toggleTagList, it will save width

    // setup sort menu
    auto menu = new QMenu(this);
    auto group = new QActionGroup(menu);
    auto datetime = new QAction(tr("Date"), group);
    datetime->setProperty("name", "datetime");
    auto title = new QAction(tr("Title"), group);
    title->setProperty("name", "title");
    auto length = new QAction(tr("Length"), group);
    length->setProperty("name", "length");
    auto ascDescGroup = new QActionGroup(menu);
    auto asc = new QAction(tr("Ascending"), ascDescGroup);
    asc->setProperty("name", "asc");
    auto desc = new QAction(tr("Descending"), ascDescGroup);
    desc->setProperty("name", "desc");
    auto sep = new QAction(menu);
    sep->setSeparator(true);

    for (auto i : {datetime, title, length, sep, asc, desc}) {
        i->setCheckable(true);
        menu->addAction(i);
        connect(i, &QAction::triggered, this, &MainWindow::onSortOrderChanged);
    }
    sorAct->setMenu(menu);
    static_cast<QToolButton*>(toolBar->widgetForAction(sorAct))->setPopupMode(QToolButton::InstantPopup);

    auto sortBy = settings->value("listSortBy").toString();
    if (sortBy == "datetime")
        datetime->setChecked(true);
    else if (sortBy == "title")
        title->setChecked(true);
    else if (sortBy == "length")
        length->setChecked(true);

    if (settings->value("listReverse").toBool())
        desc->setChecked(true);
    else
        asc->setChecked(true);

    // setup count label
    // Qt Designer doesn't allow us to add widget in toolbar
    auto p = QSizePolicy(QSizePolicy::Expanding, QSizePolicy::Maximum);
    p.setHorizontalStretch(8);
    auto spacer1 = new QWidget(toolBar);
    spacer1->setSizePolicy(p);
    toolBar->addWidget(spacer1);
    countLabel = new QLabel(toolBar);
    countLabel->setObjectName("countLabel");
    countLabel->setSizePolicy(QSizePolicy(QSizePolicy::Maximum, QSizePolicy::Maximum));
    countLabel->setMargin(4 * scaleRatio);
    toolBar->addWidget(countLabel);

    // setup search box
    searchBox = new SearchBox(this);
    auto p2 = QSizePolicy(QSizePolicy::Preferred, QSizePolicy::Fixed);
    p2.setHorizontalStretch(5);
    searchBox->setSizePolicy(p2);
    searchBox->setMinimumHeight(22 * scaleRatio);
    searchBox->setMinimumWidth(searchBox->minimumHeight() * 7.5);
    connect(searchBox->byTitleTextAct, &QAction::triggered, this, &MainWindow::setSearchBy);
    connect(searchBox->byDatetimeAct, &QAction::triggered, this, &MainWindow::setSearchBy);
    setSearchBy();
    toolBar->addWidget(searchBox);

    auto spacer2 = new QWidget(toolBar);
    spacer2->setFixedSize(2.5 * scaleRatio, 1);
    toolBar->addWidget(spacer2);

    {
        QTime t;
        t.start();
        auto l = new QTextLayout("aa");
        l->beginLayout();
        auto line = l->createLine();
        line.setLineWidth(100);
        l->endLayout();
        delete l;
        //logD()<<fontMetric(fonts.app).boundingRect(0, 0, 1988, 2000, 1041, "loading...");
        logD()<<t.elapsed();
    }
    // setup shortcuts
    searchSc = new QShortcut(QKeySequence::Find, this);
    connect(searchSc, &QShortcut::activated, [this](){ searchBox->setFocus(); });

    // delay list loading until main event loop start
    QTimer::singleShot(0, [&](){
        qApp->processEvents(QEventLoop::ExcludeUserInputEvents);  // ensure toolbar and empty list are drawn;
        diaryList->load();
    });
}

MainWindow::~MainWindow() {
}

void MainWindow::contextMenuEvent(QContextMenuEvent *e) {
    QMenu menu;
    QAction ss(tr("Edit Style Sheet"), nullptr);
    connect(&ss, &QAction::triggered, this, &MainWindow::startStyleSheetEditor);

    auto url = "file:///" + dataDir.replace("\\", "/");
    QAction dt(tr("Open Data Directory"), nullptr);
    connect(&dt, &QAction::triggered, [=](){ QDesktopServices::openUrl(url); });

    QAction ini(tr("Open config.ini"), nullptr);
    connect(&ini, &QAction::triggered, [=](){ QDesktopServices::openUrl(url+"/config.ini"); });

    QAction qt(tr("About Qt"), nullptr);
    connect(&qt, &QAction::triggered, qApp, &QApplication::aboutQt);

    menu.addActions({&ss, &dt, &ini, &qt});
    menu.exec(e->globalPos());
}

#ifdef Q_OS_WIN
bool MainWindow::nativeEvent(const QByteArray &eventType, void *message, long *result) {
    if (eventType != QByteArrayLiteral("windows_generic_MSG"))
        return false;
    auto msg = static_cast<MSG*>(message);
    if (msg->message == WM_NCRBUTTONUP || msg->message == WM_NCHITTEST) {  // NC means non-client
        auto globalPos = QPoint(GET_X_LPARAM(msg->lParam), GET_Y_LPARAM(msg->lParam));
        auto pos = mapFromGlobal(globalPos);
        auto widget = childAt(pos);
        if (widget==toolBar || widget==countLabel) {
            if (msg->message == WM_NCHITTEST) {
                *result = HTCAPTION;
            } else  {  // handle context menu
                QContextMenuEvent ev(QContextMenuEvent::Mouse, pos, globalPos);
                ev.setAccepted(true);  // same as normal one
                qApp->sendEvent(this, &ev);
                *result = 0;
            }
            return true;
        }
    }
    return false;
}
#endif

void MainWindow::closeEvent(QCloseEvent *) {
    settings->setValue("windowGeo", saveWidgetGeo(this));
    settings->setValue("tagListVisible", tagList->isVisible());
    if (tagList->isVisible())
        settings->setValue("tagListWidth", tagListWidth()/scaleRatio);
}

void MainWindow::showEvent(QShowEvent *) {
    // style polished, we can get correct height of toolbar now
    applyExtendTitleBarBg();
}

void MainWindow::changeEvent(QEvent *e) {
    QMainWindow::changeEvent(e);
    if (e->type() == QEvent::LanguageChange) {
        retranslateUi(this);
        searchBox->retranslate();
        updateCountLabel();
        tagList->load();  // "All" item
    }
}

void MainWindow::setToolBarProperty() {
    bool ex = settings->value("extendTitleBarBg").toBool();
    toolBar->setProperty("extendTitleBar", ex);
    QString type;
    if (ex) {
        if (osInfo.isWin10)
            type = "win10";  // system theme has no border
        else if (osInfo.isWin)
            type = "win";
        else
            type = "other";
    }
    toolBar->setProperty("titleBarBgType", type);
    if (isVisible()) {  // not being called by ctor
        refreshStyle(toolBar);
        refreshStyle(countLabel);  // why is this necessary?
        applyExtendTitleBarBg();
    }
}

void MainWindow::setEditorStaggerPos(Editor *editor) {
    if (!editors.isEmpty()) {
    //    lastOpenEditor = list(self.editors.values())[-1]
     //   pos = lastOpenEditor.pos() + QPoint(16, 16) * scaleRatio
      //  # can't check available screen space because of bug in pyside
       // editor.move(pos)
    }
}

void MainWindow::editorMove(int step) {
    if (editors.size() > 1)
        return;

    auto editor = editors.values()[0];
    int id = editor->getId();

    if (editor->isModified())
        return;

    auto model = diaryList->model();
    // find the index of diary which is being edited; very naive;
    // should use persistent index, but it is fast enough
    int row = -1;
    for (int r : range(model->rowCount()))
        if (model->index(r, 0).data().value<Diary>().id == id) {
            row = r;
            break;
        }
    Q_ASSERT(row != -1);

    if ((step == -1 && row == 0) ||
        (step == 1 && row == model->rowCount() - 1))
        return;
    auto idxToMove = model->index(row+step, 0);
    diaryList->clearSelection();
    diaryList->setCurrentIndex(idxToMove);
    auto thatDiary = idxToMove.data().value<Diary>();
    editor->fromDiary(thatDiary);
    editors[thatDiary.id] = editors.take(id);
}

void MainWindow::applyExtendTitleBarBg() {
    if (settings->value("extendTitleBarBg").toBool()) {
#ifdef Q_OS_WIN
        if (!QtWin::isCompositionEnabled())
            return;
        QtWin::extendFrameIntoClientArea(this, 0, toolBar->height(), 0, 0);
        setAttribute(Qt::WA_TranslucentBackground);
        // Qt5 only hack, Qt4 doesn't need this
        setAttribute(Qt::WA_NoSystemBackground, false);  // it's set by WA_TranslucentBackground
        // force background of MainWindow to be cleared before its contents being painted
        QPalette pal = palette();
        pal.setColor(QPalette::Background, Qt::transparent);
        setPalette(pal);
#endif
        auto eff = new NShadowEffect((osInfo.isWin7) ? 5 : 3, countLabel);
        eff->setColor(QColor(Qt::white));
        eff->setOffset(0, 0);
        eff->setBlurRadius(((osInfo.isWin7) ? 16 : 8) * scaleRatio);
        countLabel->setGraphicsEffect(eff);
    } else {
#ifdef Q_OS_WIN
        QtWin::resetExtendedFrame(this);
        setPalette(QApplication::palette(this));  // set palette to default one
#endif
        auto eff = countLabel->graphicsEffect();
        if (eff) {
            countLabel->setGraphicsEffect(nullptr);
            delete eff;
        }
    }
}

int MainWindow::tagListWidth() {
    return splitter->sizes()[0];
}

void MainWindow::setTagListWidth(int w) {
    splitter->setSizes({ w, width()-w });
}

void MainWindow::toggleTagList(bool show, bool animated) {
    if (animated)
        tagList->setMinimumWidth(1);
    if (show) {
        if (tagListAni->state() == QPropertyAnimation::Running)
            tagListAni->stop();
        else
            tagList->showAndLoad();
        auto tListW = settings->value("tagListWidth").toInt();
        tListW = (tListW) ? tListW * scaleRatio : width() * 0.2;
        if (animated) {
            tagListAni->setStartValue(tagListWidth());  // may continue stopped ani
            tagListAni->setEndValue(tListW);
            tagListAni->start();
        } else
            setTagListWidth(tListW);
    } else {
        if (tagListAni->state() == QPropertyAnimation::Running)
            tagListAni->stop();
        else
            settings->setValue("tagListWidth", tagListWidth()/scaleRatio);
        if (animated) {
            tagListAni->setStartValue(tagListWidth());
            tagListAni->setEndValue(0);
            tagListAni->start();
        } else
            tagList->hide();
    }
}

void MainWindow::startStyleSheetEditor() {
    if (qssEditor)
        return qssEditor->activateWindow();
    qssEditor = new QssEditor(this);
    qssEditor->resize(QSize(600, 550) * scaleRatio);
    qssEditor->show();
}

void MainWindow::updateCountLabel() {
    countLabel->setText(tr("%1 diaries").arg(diaryList->model()->rowCount()));
}

void MainWindow::onSortOrderChanged(bool checked) {
    auto name = sender()->property("name");
    if (name == "asc" || name == "desc")
        settings->setValue("listReverse", name=="desc");
    else if (checked)
        settings->setValue("listSortBy", name);
    diaryList->sort();
}

void MainWindow::onDiaryListGoto() {
    if (!searchBox->text().isEmpty())
        searchBox->clear();
    if (!tagList->selectedItems().isEmpty())
        tagList->setCurrentRow(0);
    diaryList->scrollTo(diaryList->currentIndex(), QListView::PositionAtCenter);
}

void MainWindow::startEditor() {
    const auto diary = diaryList->currentIndex().data().value<Diary>();
    if (editors.contains(diary.id))
        editors[diary.id]->activateWindow();
    else {
        auto e = new Editor();
        e->fromDiary(diary);
        setEditorStaggerPos(e);
        editors[diary.id] = e;
        connect(e, &Editor::closed, this, &MainWindow::onEditorClosed);
        auto pre = [&]() { editorMove(-1); };
        auto next = [&]() { editorMove(1); };
        connect(e->preSc, &QShortcut::activated, pre);
        connect(e->quickPreSc, &QShortcut::activated, pre);
        connect(e->nextSc, &QShortcut::activated, next);
        connect(e->quickNextSc, &QShortcut::activated, next);
        e->show();
    }
}

void MainWindow::startEditorNew() {
    if (editors.contains(-1))
        editors[-1]->activateWindow();
    else {
        auto e = new Editor();
        setEditorStaggerPos(e);
        editors[-1] = e;
        connect(e, &Editor::closed, this, &MainWindow::onEditorClosed);
        e->show();
    }
}

// Write editor's data to model and database, and destroy editor
void MainWindow::onEditorClosed(int id, bool needSave) {
    auto editor = editors[id];
    bool newDiary = id == -1;
    if (needSave) {
        qApp->setOverrideCursor(QCursor(Qt::WaitCursor));
        auto diary = editor->toDiary();
        diaryList->saveDiary(diary, !editor->tagModified);
        if (newDiary)
            updateCountLabel();
        if (editor->tagModified)
            tagList->reload();
        qApp->restoreOverrideCursor();
    }
    delete editor;
    editors.remove(id);
}

void MainWindow::setSearchBy() {
    if (sender())  // not called in ctor
        disconnect(searchBox, &SearchBox::contentChanged, nullptr, nullptr);
    if (sender() == searchBox->byTitleTextAct || sender() == nullptr)
        connect(searchBox, &SearchBox::contentChanged, diaryList, &DiaryList::setFilterBySearchStr);
    else
        connect(searchBox, &SearchBox::contentChanged, diaryList, &DiaryList::setFilterByDatetime);
}

void MainWindow::startHeatMap() {
    if (heatMap)
        return heatMap->activateWindow();

    heatMap = new HeatMap(this);
    heatMap->setObjectName("heatMap");
    heatMap->setFont(fonts.datetime);
    heatMap->resize(size());
    heatMap->move(pos() + QPoint(12, 12)*scaleRatio);

    // some languages have more info in single character
    // ratios are from http://www.sonasphere.com/blog/?p=1319
    static const QMap<QLocale::Language, double> languageRatio = {
        {QLocale::Chinese, 1}, {QLocale::English, 4}, {QLocale::Japanese, 1.5}
    };
    auto ratio = languageRatio.value(QLocale().language(), 1.6);
    auto dsEnd = QString(" ") + qApp->translate("HeatMap", "(charactors)");
    QStringList ds = {QString("0")+dsEnd, QString("< %1").arg(200*ratio)+dsEnd,
                      QString("< %1").arg(550*ratio)+dsEnd,
                      QString(">= %1").arg(550*ratio)+dsEnd};
    heatMap->sample->setDescriptions(ds);
    heatMap->view->cellColorFunc = [=](int data, const QList<QColor> &cellColors) {
        int d = data / ratio;
        if (data == 0)
            return cellColors[0];
        else if (d < 200)
            return cellColors[1];
        else if (d < 550)
            return cellColors[2];
        else
            return cellColors[3];
    };

    QHash<QDate, int> date2diary;
    auto m = diaryList->model();
    for (int r : range(m->rowCount())) {
        const auto diary = m->data(m->index(r, 0)).value<Diary>();
        date2diary[diary.datetime.date()] = diary.text.length();
    }
    heatMap->view->cellDataFunc = [=](QDate date) {
        return date2diary.value(date, 0);
    };

    heatMap->show();
}

void MainWindow::deleteSelectedDiary() {
    if (!diaryList->hasSelection())
        return;
    QMessageBox msg(this);
    auto okBtn = msg.addButton(qApp->translate("Dialog", "Delete"), QMessageBox::AcceptRole);
    msg.setIcon(QMessageBox::Question);
    msg.addButton(qApp->translate("Dialog", "Cancel"), QMessageBox::RejectRole);
    msg.setWindowTitle(tr("Delete diaries"));
    msg.setText(tr("Selected diaries will be deleted permanently!"));
    msg.exec();

    if (msg.clickedButton() == okBtn) {
        diaryList->deleteSelected();
        tagList->reload();  // tags might changed
    }
}
