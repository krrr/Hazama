"""Using GitHub release API to check update and download new version.
Download is Windows only. Old version will be renamed on-the-fly,
and new version extracted (it's a hack, and doesn't work on XP;
not sure whether it will work on Vista)"""
import os
import json
import re
import logging
import hazama
import zipfile
import time
from datetime import date, timedelta
from urllib.request import urlopen, Request
from collections import namedtuple
from PyQt5.QtCore import QThread, pyqtSignal
from hazama.config import appPath, settings, SOCKET_TIMEOUT


_GITHUB_API_URL = 'https://api.github.com/repos/krrr/Hazama/releases/latest'

UpdateInfo = namedtuple('Update', ['version', 'note', 'url', 'note_html'])


def verToTuple(s):
    if s.startswith('v'):
        s = s[1:]
    return tuple(map(int, s.split('.')))


def _note2html(s):
    out = ['<ul>']
    for l in s.split('\n'):
        if l[:2] in ['* ', '+ ', '- ']:
            out.append('<li>%s</li>' % l[2:])
    out.append('</ul>')
    return '\n'.join(out)


def textProgressBar(iteration, total, sep='&nbsp;', barLen=30):
    """
    from https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
    """
    filledLen = round(barLen * iteration / total)
    percent = 100 * (iteration / total)
    bar = '▇' * filledLen + '▁' * (barLen - filledLen)
    return '▕' + bar + '▏' + sep + '{:4.1f}'.format(percent) + '%'


def _urlopenErrSimplify(e):
    e = str(e)
    if e.startswith('<urlopen error'):
        return e[15:-1]
    return e


def cleanBackup():
    try:
        for dirname, __, filenames in os.walk(appPath):
            for i in filter(lambda x: x.endswith('.bak'), filenames):
                p = os.path.join(dirname, i)
                logging.info('removing update backup: %s' % p)
                os.remove(p)
    except Exception as e:
        logging.warning('failed to clean update backup: %s' % e)


def isCheckNeeded():
    """Return False if checked within 3days. Creating thread will cause
    subtle slowdown, so avoid doing it very often."""
    if not settings['Update'].getboolean('autoCheck'):
        return False
    last = settings['Update'].get('lastCheckDate', '1970-01-01')
    return str(last) < str(date.today() - timedelta(days=3))


def _setCheckUpdateTask(to=None):
    global checkUpdateTask
    checkUpdateTask = to


def _setInstallUpdateTask(to=None):
    global installUpdateTask
    installUpdateTask = to


# QThread's class variables has some strange write delay, so use module variable here
checkUpdateTask = installUpdateTask = None
foundUpdate = None


# all members and methods except run() of QThread reside in the old thread
class CheckUpdate(QThread):
    DummyNote = '**Changes**\n* wwww\n*ww\n**NEW**\n* aaa\n*bbb'
    DummyResult = UpdateInfo('9.9.9', DummyNote,
                             'https://github.com/krrr/krrr.github.io/releases/download/v1.0.2/a.zip',
                             _note2html(DummyNote))
    failed = pyqtSignal(str)
    succeeded = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.result = None

        # __init__ should only be called from UI thread, so locking is unnecessary
        if checkUpdateTask:
            raise Exception('instance exists')
        _setCheckUpdateTask(self)
        self.finished.connect(_setCheckUpdateTask)

    def run(self):
        logging.info('update checking started')
        try:
            resp = urlopen(Request(_GITHUB_API_URL,
                                   headers={'User-Agent': 'hazama-updater',
                                            'Accept': 'application/vnd.github.v3+json'}),
                           timeout=SOCKET_TIMEOUT)
            if resp.status != 200:
                raise Exception('HTTP status code is not OK (%s)' % resp.status)

            release = json.loads(resp.read().decode('utf-8'))
            ver = verToTuple(release['tag_name'])
            currentVer = verToTuple(hazama.__version__)
            settings['Update']['lastCheckDate'] = str(date.today())
            if ver <= currentVer or ver <= verToTuple(settings['Update']['newestIgnoredVer']):
                logging.info('update ignored: %s' % release['tag_name'])
                return self.succeeded.emit()

            update = None
            for i in release['assets']:
                r = re.match(r'hazama-v[0-9.]+-win\.zip', i['name'])
                if not r:
                    continue
                # tag_name looks like "v1.0.0"
                update = UpdateInfo(release['tag_name'][1:], release['body'], i['url'],
                                    _note2html(release['body']))
                break

            logging.info('update found: %s' % release['tag_name'])
            self.result = update
            global foundUpdate
            foundUpdate = update
            self.succeeded.emit()
        except Exception as e:
            logging.error('check-update failed: %s' % e)
            self.failed.emit(_urlopenErrSimplify(e))

    def disConn(self):
        self.succeeded.disconnect()
        self.failed.disconnect()


class InstallUpdate(QThread):
    """Download and install update."""
    progress = pyqtSignal(int, int)  # received, total
    downloadFinished = pyqtSignal()
    failed = pyqtSignal(str)
    succeeded = pyqtSignal()

    def __init__(self, updateInfo):
        super().__init__()
        self.result = None
        self.canceled = False
        self.updateInfo = updateInfo

        # __init__ should only be called from UI thread, so locking is unnecessary
        if installUpdateTask:
            raise Exception('instance exists')
        _setInstallUpdateTask(self)
        self.finished.connect(_setInstallUpdateTask)

    def run(self):
        f = path = None
        try:
            resp = urlopen(Request(self.updateInfo.url,
                                   headers={'Accept': 'application/octet-stream',
                                            'User-Agent': 'hazama-updater'}),
                           timeout=SOCKET_TIMEOUT)
            if resp.status != 200:
                raise Exception('HTTP status code is not OK (%s)' % resp.status)

            length = int(resp.headers.get('Content-Length', -1))
            received = 0
            path = os.path.join(os.environ['TEMP'], 'hazama_update.zip')
            f = open(path, 'w+b')

            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                if self.canceled:
                    return
                self.progress.emit(received, length)
                received += len(chunk)
                f.write(chunk)
            self.downloadFinished.emit()

            # following code can't be canceled once executed
            archive = zipfile.ZipFile(f)
            for i in archive.infolist():
                if i.filename.endswith('/'):  # skip directory
                    continue
                target = os.path.join(appPath, i.filename)
                mtime = time.mktime(i.date_time + (0, 0, -1))

                if os.path.isfile(target):
                    stat = os.stat(target)
                    # zip doesn't support time zone, and its time resolution is 2sec
                    if abs(stat.st_mtime - mtime) <= 2 and stat.st_size == i.file_size:
                        logging.debug('skipping %s' % i.filename)
                        continue
                    bak = target+'.bak'
                    if os.path.isfile(bak):
                        os.remove(bak)
                    os.rename(target, bak)
                logging.info('extracting %s' % i.filename)
                archive.extract(i, appPath)
                os.utime(target, (mtime, mtime))

            settings['Update']['needClean'] = str(True)
            archive.close()
            self.succeeded.emit()
        except Exception as e:
            logging.error('download-update failed: %s' % e)
            self.failed.emit(_urlopenErrSimplify(e))
        finally:
            if f:
                f.close()
                os.remove(path)

    def disConn(self):
        self.progress.disconnect()
        self.succeeded.disconnect()
        self.failed.disconnect()
