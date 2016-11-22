import sys
import os
import time
import logging
import PySide
import hazama.ui.res_rc  # load resources, let showErrors have icons
from PySide.QtGui import *
from PySide.QtCore import *
from hazama.config import (settings, appPath, isWin, isWinVistaOrLater, isWin8OrLater,
                           CUSTOM_STYLESHEET_DELIMIT)


# qApp global var is None before entering event loop, use QApplication.instance() instead

locale = sysLocale = None
# datetimeFmt may not contain time part (by default)
dateFmt = datetimeFmt = fullDatetimeFmt = None
font = None
scaleRatio = None
_trans = _transQt = None  # Translator, just used to keep reference


dbDatetimeFmtQt = 'yyyy-MM-dd HH:mm'


def datetimeToQt(s):
    return locale.toDateTime(s, dbDatetimeFmtQt)


def datetimeTrans(s, stripTime=False):
    """Localize datetime in database format."""
    dt = QDateTime.fromString(s, dbDatetimeFmtQt)
    return locale.toString(dt, dateFmt if stripTime else datetimeFmt)


def currentDatetime():
    """Return current datetime in database format."""
    return time.strftime('%Y-%m-%d %H:%M')


def readRcTextFile(path):
    """Read whole text file from qt resources system."""
    assert path.startswith(':/')
    f = QFile(path)
    if not f.open(QFile.ReadOnly | QFile.Text):
        raise FileNotFoundError('failed to read rc text %s' % path)
    text = str(f.readAll())
    f.close()
    return text


def setTranslationLocale():
    global locale, sysLocale, _trans, _transQt
    lang = settings['Main'].get('lang')
    sysLocale = QLocale.system()
    if not lang:
        lang = settings['Main']['lang'] = locale.name()
    if lang == sysLocale.name():
        locale = sysLocale
    else:  # special case: application language is different from system's
        locale = QLocale(lang)
        QLocale.setDefault(locale)
    langPath = os.path.join(appPath, 'lang')
    logging.info('set translation ' + lang)

    _trans = QTranslator()
    _trans.load(lang, langPath)
    _transQt = QTranslator()
    if hasattr(sys, 'frozen'):
        _transQt.load('qt_' + lang, langPath)
    else:
        _transQt.load('qt_' + lang, QLibraryInfo.location(QLibraryInfo.TranslationsPath))
    for i in [_trans, _transQt]: QApplication.instance().installTranslator(i)

    global dateFmt, datetimeFmt, fullDatetimeFmt
    timeFmt = settings['Main'].get('timeFormat')
    dateFmt = settings['Main'].get('dateFormat') or locale.dateFormat()
    datetimeFmt = (dateFmt + ' ' + timeFmt) if timeFmt else dateFmt
    # use hh:mm because locale.timeFormat will include seconds
    fullDatetimeFmt = dateFmt + ' ' + (timeFmt or 'hh:mm')


def showErrors(type_, *args, exit_=False):
    """Show variety of error dialogs."""
    app = QApplication.instance()
    if not app:
        app = init()
    {'dbError': lambda hint='': QMessageBox.critical(
        None,
        app.translate('Errors', 'Diary book inaccessible'),
        app.translate('Errors', 'Diary book seems corrupted. You may have to '
                                'recover it from backups.\n\nSQLite3: %s') % hint),
     'dbLocked': lambda: QMessageBox.warning(
         None,
         app.translate('Errors', 'Multiple access error'),
         app.translate('Errors', 'This diary book is already open.')),
     'cantFile': lambda filename: QMessageBox.critical(
         None,
         app.translate('Errors', 'File inaccessible'),
         app.translate('Errors', 'Failed to access %s') % filename),
     'fileCorrupted': lambda filename: QMessageBox.critical(
         None,
         app.translate('Errors', 'File corrupted'),
         app.translate('Errors', '%s is corrupted, please delete or fix it.') % filename)
     }[type_](*args)

    if exit_:
        sys.exit(-1)


def setStdEditMenuIcons(menu):
    """Add system theme icons to QLineEdit and QTextEdit context-menu.
    :param menu: QMenu generated by createStandardContextMenu
    """
    acts = menu.actions()
    if len(acts) < 9: return
    (undo, redo, __, cut, copy, paste, delete, __, sel, *__) = acts
    undo.setIcon(QIcon.fromTheme('edit-undo'))
    redo.setIcon(QIcon.fromTheme('edit-redo'))
    cut.setIcon(QIcon.fromTheme('edit-cut'))
    copy.setIcon(QIcon.fromTheme('edit-copy'))
    paste.setIcon(QIcon.fromTheme('edit-paste'))
    delete.setIcon(QIcon.fromTheme('edit-delete'))
    sel.setIcon(QIcon.fromTheme('edit-select-all'))


def setStyleSheet():
    """If -stylesheet not in sys.argv, append custom.qss(if exists) to default one and
    load it. Otherwise load the one in sys.argv"""
    if '-stylesheet' in sys.argv:
        logging.info('override default StyleSheet by command line arg')
    else:
        ss = [readRcTextFile(':/default.qss')]
        # append theme part
        if settings['Main']['theme'] == 'colorful':
            ss.append(readRcTextFile(':/colorful.qss'))
            scheme = settings['ThemeColorful']['colorScheme']
            if scheme != 'green':
                ss.append(readRcTextFile(':/colorful-%s.qss' % scheme))
        # load custom
        ss.append(CUSTOM_STYLESHEET_DELIMIT)
        if os.path.isfile('custom.qss'):
            logging.info('set custom StyleSheet')
            with open('custom.qss', encoding='utf-8') as f:
                ss.append(f.read())

        QApplication.instance().setStyleSheet(''.join(ss))


def winDwmExtendWindowFrame(winId, topMargin):
    """Extend background of title bar to toolbar. Only available on Windows
    because it depends on DWM. winId is PyCapsule object, which storing HWND."""
    if not isDwmUsable(): return
    from ctypes import (c_int, byref, pythonapi, c_void_p, c_char_p, py_object,
                        windll, Structure)

    # define prototypes & structures
    class Margin(Structure):
        _fields_ = [('left', c_int), ('right', c_int),
                    ('top', c_int), ('bottom', c_int)]
    pythonapi.PyCapsule_GetPointer.restype = c_void_p
    pythonapi.PyCapsule_GetPointer.argtypes = [py_object, c_char_p]

    winId = pythonapi.PyCapsule_GetPointer(winId, None)
    margin = Margin(0, 0, topMargin, 0)
    windll.dwmapi.DwmExtendFrameIntoClientArea(winId, byref(margin))

    return True


def isDwmUsable():
    """Check whether winDwmExtendWindowFrame usable."""
    if not isWin:
        return False
    if isWin8OrLater:
        # windows 8 or later always have DWM composition enabled, but API used below depends
        # on manifest file (we doesn't have it)
        return True
    elif not isWinVistaOrLater:
        return False
    else:
        from ctypes import byref, windll, c_bool

        b = c_bool()
        ret = windll.dwmapi.DwmIsCompositionEnabled(byref(b))
        return ret == 0 and b.value


def fixWidgetSizeOnHiDpi(widget):
    """Simply resize current size according to DPI. Should be called after setupUi."""
    if scaleRatio > 1:
        widget.resize(widget.size() * scaleRatio)
        widget.setMinimumSize(widget.minimumSize() * scaleRatio)  # prevent over sizing after resize


def saveWidgetGeo(widget):
    return '%s,%s' % (widget.saveGeometry().toHex(), scaleRatio)


def restoreWidgetGeo(widget, geoStr):
    if not geoStr or geoStr.count(',') != 1:
        return fixWidgetSizeOnHiDpi(widget)

    a, b = geoStr.split(',')
    success = widget.restoreGeometry(QByteArray.fromHex(a))
    ratio = scaleRatio / float(b)
    if success and abs(ratio - 1) > 0.01:
        widget.move(widget.pos() * ratio)
        widget.resize(widget.size() * ratio)


def makeQIcon(*filenames, scaled2x=False):
    """A Shortcut to construct a QIcon which has multiple images. Try to add all sizes
    (xx.png & xx-big.png & xx-mega.png) when only one filename supplied."""
    ico = QIcon()
    if len(filenames) == 1:
        fname = filenames[0]
        assert '.' in fname
        b, ext = fname.rsplit('.')

        ico.addFile(fname)
        ico.addFile(b + '-big.' + ext)  # fails silently when file not exist
        if scaled2x and scaleRatio > 1.5:
            origin = QPixmap(fname)
            ico.addPixmap(origin.scaled(origin.size() * 2))
        else:
            ico.addFile(b + '-mega.' + ext)
    else:
        for i in filenames:
            ico.addFile(i)
    return ico


def markIcon(ico, size, markFName):
    sz = size * scaleRatio
    origin = ico.pixmap(sz)
    painter = QPainter(origin)
    painter.drawPixmap(0, 0, QPixmap(markFName).scaled(sz))
    painter.end()  # this should be called at destruction, but... critical error everywhere?
    ico.addPixmap(origin)


def refreshStyle(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class Fonts:
    """Manage all fonts used in application"""
    preferredFonts = {
        'zh_CN': ('Microsoft YaHei', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC',
                  'Source Han Sans CN Normal'),
        'ja_JP': ('Meiryo', 'Noto Sans CJK JP', '游ゴシック Medium'),
        'zh_TW': ('Microsoft JhengHei', 'Noto Sans CJK TC')}

    def __init__(self):
        # all fonts have userSet attribute
        self.title = QFont()
        self.datetime = QFont()
        self.text = QFont()
        self.default = None
        self.default_m = self.title_m = self.datetime_m = self.text_m = None

    def load(self):
        self.default = QApplication.instance().font()
        saved = settings['Font'].get('default')
        preferred = None if saved else self.getPreferredFont()
        self.default.userSet = bool(saved)
        if saved:
            self.default.fromString(saved)
        elif preferred:
            self.default = preferred
        logging.debug('app font %s' % self.default)
        QApplication.instance().setFont(self.default)

        for i in ('title', 'datetime', 'text'):
            f = getattr(self, i)
            f.fromString(settings['Font'].get(i))
            f.userSet = True
            if not f.exactMatch():
                # document says f.family() == '' will use app font, but it not work on Linux
                # userSet attr is for this
                f.setFamily(self.default.family())
                f.userSet = False

        for i in ('title', 'datetime', 'text', 'default'):
            # passing None as 2nd arg to QFontMetrics make difference on high DPI
            setattr(self, i+'_m', QFontMetrics(getattr(self, i), None))

    @classmethod
    def getPreferredFont(cls):
        """Return preferred font according to language and platform."""
        # 1. get sans-serif CJ fonts that looks good on HiDPI
        # 2. fix when app font doesn't match system's, this will cause incorrect lineSpacing (
        # an attempt to use QFontDatabase to auto get right font was failed)
        if isWin and scaleRatio == 1 and settings['Main']['theme'] == '1px-rect':
            # old theme looks fine with default bitmap fonts only on normal DPI (SimSun)
            return None

        lst = cls.preferredFonts.get(locale.name() if locale.language() != sysLocale.language() else
                                     sysLocale.name())
        f = QApplication.instance().font()
        for i in lst:
            f.setFamily(i)
            if f.exactMatch():
                return f

        return None


def init():
    logging.debug('PySide ver: %s  (lib path: %s)', PySide.__version__,
                  QLibraryInfo.location(QLibraryInfo.LibrariesPath))
    app = QApplication(sys.argv)
    app.setWindowIcon(makeQIcon(':/appicon-24.png', ':/appicon-48.png'))

    global scaleRatio
    scaleRatio = app.desktop().logicalDpiX() / 96  # when will x != y happen?
    logging.debug('DPI scale ratio %s' % scaleRatio)

    setTranslationLocale()
    global font
    font = Fonts()
    font.load()

    setStyleSheet()
    return app
