QT += sql widgets
win32:QT += winextras


TARGET = hazama
VERSION = 1.1.0
TEMPLATE = app
CONFIG += c++14


# The following define makes your compiler emit warnings if you use
# any feature of Qt which as been marked as deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS

SOURCES += \
        main.cpp \
        mainwindow.cpp \
    diarymodel.cpp \
    diarylist.cpp \
    db.cpp \
    fonts.cpp \
    customobjects/ntextdocument.cpp \
    customobjects/multilineelidelabel.cpp \
    taglist.cpp \
    searchbox.cpp \
    customobjects/nshadoweffect.cpp \
    qsseditor.cpp \
    diarylistscrollbar.cpp \
    diarydelegates.cpp \
    updater.cpp \
    tagdelegates.cpp \
    heatmap.cpp \
    editor.cpp \
    customobjects/ntextedit.cpp \
    customobjects/datetimedialog.cpp \
    globals.cpp

HEADERS += \
        mainwindow.h \
    diarymodel.h \
    diarylist.h \
    db.h \
    globals.h \
    customobjects/ntextdocument.h \
    customobjects/multilineelidelabel.h \
    taglist.h \
    customobjects/qlineeditmenuicon.h \
    searchbox.h \
    customobjects/nshadoweffect.h \
    cppassist.h \
    qsseditor.h \
    diarylistscrollbar.h \
    diarydelegates.h \
    taglistdelegates.h \
    customobjects/elidelabel.h \
    updater.h \
    heatmap.h \
    editor.h \
    customobjects/ntextedit.h \
    customobjects/datetimedialog.h \
    customobjects/formattermixin.h

FORMS += \
    mainwindow.ui \
    editor.ui

RC_ICONS = res/appicon/appicon.ico

RESOURCES += \
    res/res.qrc

win32-msvc:QMAKE_CXXFLAGS += /utf-8

PRECOMPILED_HEADER = pre.h
