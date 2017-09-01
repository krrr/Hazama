#pragma once
#include <QFrame>
#include <ui_editor.h>
#include "diarymodel.h"

class QShortcut;

class Editor : public QFrame, public Ui::editor {
    Q_OBJECT
public:
    bool readOnly = false;
    bool noSave = false;
    bool timeModified=false, tagModified=false;
    QShortcut *closeSaveSc, *closeNoSaveSc, *quickCloseSc;
    QShortcut *preSc, *quickPreSc, *nextSc, *quickNextSc;

    Editor(QWidget *parent = nullptr);
#ifdef Q_OS_WIN  // custom buttom area for Windows
    bool nativeEvent(const QByteArray &eventType, void *message, long *result);
#endif
    void showEvent(QShowEvent *e);
    void closeEvent(QCloseEvent *e);
    void mousePressEvent(QMouseEvent *e);
    void setReadOnly(bool to);
    bool isModified();
    void fromDiary(const Diary &d);
    int getId() { return id; }
    Diary toDiary();

signals:
    void closed(int diaryId, bool needSave);

public slots:
    void closeNoSave() {
        noSave = true;
        close();
    }

private:
    int id = -1;
    QDateTime datetime;

    void applyExtendTitleBarBg();

private slots:
    void editDateTime();
};
