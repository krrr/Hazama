/*
 Copyright (C) 2017 krrr <guogaishiwo@gmail.com>

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU General Public License for more details.
*/
#include <iostream>
#include "mainwindow.h"
#include <QApplication>
#include <QDesktopWidget>
#include "globals.h"
#include "db.h"

/*
 ---- Project Coding Guide ----
  - Class definition order: ctor, Qt's methods, methods, slots

 ---- Notes ----
  - StyleSheets using dynamic property require (un)polish to take effect
  - Subclass of QWidget refuse to paint QSS background. Use QFrame or set WA_StyledBackground
*/

static void customMsgHandler(QtMsgType type, const QMessageLogContext &, const QString &msg) {
    auto localMsg = msg.toLocal8Bit();
    switch (type) {
    case QtDebugMsg:
        std::cout << "DEBUG: " << localMsg.constData() << std::endl;
        break;
    case QtInfoMsg:
        std::cout << "INFO: " << localMsg.constData() << std::endl;
        break;
    case QtWarningMsg:
        std::cout << "WRANING: " << localMsg.constData() << std::endl;
        break;
    case QtCriticalMsg: case QtFatalMsg:
        std::cout << "ERROR: " << localMsg.constData() << std::endl;
        break;
    }
}

int main(int argc, char *argv[]) {
    QTime t;
    t.start();
    // Finding Memory Leaks Using the CRT Library
#if defined(_WIN32) && defined(_DEBUG)
    #include <crtdbg.h>
    _CrtSetDbgFlag(_CrtSetDbgFlag(_CRTDBG_REPORT_FLAG)|_CRTDBG_LEAK_CHECK_DF);
#endif

    qInstallMessageHandler(customMsgHandler);

    QApplication a(argc, argv);
    a.setApplicationName("Hazama");
    a.setApplicationVersion(APP_VER);
    a.setOrganizationName("krrr");
#ifndef Q_OS_WIN
    a.setWindowIcon(makeQIcon({":/appicon-24.png", ":/appicon-48.png"}));
#endif

    dataDir = getDataDir();
    if (!initSettings())
        return -1;
    fonts.load();
    scaleRatio = qApp->desktop()->logicalDpiX() / 96.0;  // when will x != y happen?
    logI() << "DPI scale ratio" << scaleRatio;
    loadStyleSheet();
    setTranslationLocale();

    if (!initDb())
        return -1;

    // save settings before being terminated by OS (such as logging off on Windows).
    a.connect(&a, &QApplication::aboutToQuit, [](){
        settings->sync();
        database()->close();
    });

    MainWindow w;
    w.show();
    logD() << "main() took" << t.elapsed() << "ms";
    return a.exec();
}
