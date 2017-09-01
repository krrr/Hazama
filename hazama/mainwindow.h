#pragma once
#include <QMainWindow>
#include <QPointer>
#include "editor.h"
#include "ui_mainwindow.h"

class QLabel;
class SearchBox;
class QPropertyAnimation;
class QShortcut;
class QssEditor;
class HeatMap;


class MainWindow : public QMainWindow, public Ui::mainWindow {
    Q_OBJECT
    Q_PROPERTY(int tagListWidth READ tagListWidth WRITE setTagListWidth)

public:
    MainWindow(QWidget *parent = 0);
    ~MainWindow();
    void contextMenuEvent(QContextMenuEvent *event);
#ifdef Q_OS_WIN  // custom tool bar for Windows
    bool nativeEvent(const QByteArray &eventType, void *message, long *result);
#endif
    void closeEvent(QCloseEvent *e);
    void showEvent(QShowEvent *e);
    void changeEvent(QEvent *e);
    int tagListWidth();
    void setTagListWidth(int w);

public slots:
    void setSearchBy();
    void onSortOrderChanged(bool checked);
    void toggleTagList(bool show) { toggleTagList(show, true); }
    void updateCountLabel();
    /* Scroll the list to the original position (unfiltered) of an entry */
    void onDiaryListGoto();
    void startEditor();
    void startEditorNew();
    void onEditorClosed(int id, bool needSave);

private:
    QLabel *countLabel;
    QPointer<QssEditor> qssEditor;
    QPointer<HeatMap> heatMap;
    QShortcut *searchSc;
    SearchBox *searchBox;
    QMap<int, Editor*> editors;
    QPropertyAnimation *tagListAni;
    int lastTagListHideW = -1;

    void toggleTagList(bool show, bool animated);
    void applyExtendTitleBarBg();
    void setToolBarProperty();
    void setEditorStaggerPos(Editor *editor);
    void editorMove(int step);

private slots:
    void startStyleSheetEditor();
    void startHeatMap();
    void deleteSelectedDiary();
};
