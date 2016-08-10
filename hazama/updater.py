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
from urllib.request import urlopen, Request
from collections import namedtuple
from PySide.QtCore import QThread, Signal
from hazama.config import appPath, settings, SOCKET_TIMEOUT


_GITHUB_API_URL = 'https://api.github.com/repos/krrr/krrr.github.io/releases/latest'

UpdateInfo = namedtuple('Update', ['version', 'note', 'url', 'note_html'])


def verToTuple(s):
    if s.startswith('v'):
        s = s[1:]
    return tuple(map(int, s.split('.')))


def note2html(s):
    out = ['<ul>']
    for l in s.split('\n'):
        if l[:2] in ['* ', '+ ', '- ']:
            out.append('<li>%s</li>' % l[2:])
    out.append('</ul>')
    return '\n'.join(out)


def textProgressBar(iteration, total, prefix='', suffix='', bar_len=30):
    """
    from https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
    """
    filled_len = round(bar_len * iteration / total)
    percent = 100 * (iteration / total)
    bar = '▇' * filled_len + '▁' * (bar_len - filled_len)
    return prefix + ' |' + bar + '| ' + '{:4.1f}'.format(percent) + '% ' + suffix


def urlopenErrSimplify(e):
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


# QThread's class variables has some strange write delay, so use module variable here
checkUpdateTask = installUpdateTask = None
foundUpdate = None


# all members and methods except run() of QThread reside in the old thread
class CheckUpdate(QThread):
    DummyNote = '**Changes**\n* wwww\n*ww\n**NEW**\n* aaa\n*bbb'
    DummyResult = UpdateInfo('9.9.9', DummyNote,
                             'https://github.com/krrr/krrr.github.io/releases/download/v1.0.2/a.zip',
                             note2html(DummyNote))
    failed = Signal(str)
    succeeded = Signal()

    def __init__(self):
        super().__init__()
        self.result = None

        # __init__ should only be called from UI thread, so locking is unnecessary
        global checkUpdateTask
        if checkUpdateTask:
            raise Exception('instance exists')
        checkUpdateTask = self
        self.finished.connect(lambda: globals().update(checkUpdateTask=None))

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
                                    note2html(release['body']))
                break

            logging.info('update found: %s' % release['tag_name'])
            self.result = update
            global foundUpdate
            foundUpdate = update
            self.succeeded.emit()
        except Exception as e:
            logging.error('check-update failed: %s' % e)
            self.failed.emit(urlopenErrSimplify(e))

    def disConn(self):
        self.succeeded.disconnect()
        self.failed.disconnect()


class InstallUpdate(QThread):
    progress = Signal(int, int)  # received, total
    downloadFinished = Signal()
    failed = Signal(str)
    succeeded = Signal()

    def __init__(self, updateInfo):
        super().__init__()
        self.result = None
        self.canceled = False
        self.updateInfo = updateInfo

        # __init__ should only be called from UI thread, so locking is unnecessary
        global installUpdateTask
        if installUpdateTask:
            raise Exception('instance exists')
        installUpdateTask = self
        self.finished.connect(lambda: globals().update(installUpdateTask=None))

    def run(self):
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
            self.failed.emit(urlopenErrSimplify(e))

    def disConn(self):
        self.progress.disconnect()
        self.succeeded.disconnect()
        self.failed.disconnect()
