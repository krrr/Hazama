from PySide.QtGui import *
from PySide.QtCore import *
from .configdialog_ui import Ui_Settings
from . import font
from config import settings
import logging


class ConfigDialog(QDialog, Ui_Settings):
    lang2index = {'en': 0, 'zh_CN': 1, 'ja': 2}  # index used in lang combo
    index2lang = {b: a for (a, b) in lang2index.items()}

    def __init__(self, parent=None):
        super(ConfigDialog, self).__init__(parent, Qt.WindowTitleHint)
        self.mainw = parent
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.setFont(font.sys)
        # load settings
        self.aindCheck.setChecked(settings['Editor'].getint('autoindent', 1))
        self.tfocusCheck.setChecked(settings['Editor'].getint('titlefocus', 0))
        self.bkCheck.setChecked(settings['Main'].getint('backup', 1))
        self.langCombo.setCurrentIndex(self.lang2index[
                                       settings['Main'].get('lang', 'en')])

    def accept(self):
        settings['Editor']['autoindent'] = str(self.aindCheck.isChecked().real)
        settings['Editor']['titlefocus'] = str(self.tfocusCheck.isChecked().real)
        settings['Main']['backup'] = str(self.bkCheck.isChecked().real)
        lang = self.index2lang[self.langCombo.currentIndex()]
        if settings['Main'].get('lang', 'en') != lang:
            settings['Main']['lang'] = lang
            logging.info('Settings saved')
            self.mainw.needRestart.emit()
            del self.mainw
        else:
            logging.info('Settings saved')
            self.close()

    @Slot()
    def on_exportBtn_clicked(self):
        export_all = not bool(self.exportOption.currentIndex())
        txtpath, _type = QFileDialog.getSaveFileName(self,
            self.tr('Export Diary'), os.getcwd(),
            self.tr('Plain Text (*.txt);;Rich Text (*.rtf)'))
        if txtpath == '': return    # dialog canceled
        if _type.endswith('txt)'):
            selected = (None if export_all else
                        [i.data(2) for i in self.mainw.nlist.selectedItems()])
            nikki.exporttxt(txtpath, selected)

