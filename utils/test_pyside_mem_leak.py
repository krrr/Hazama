"""Do not pass parent to some object that isn't sub-class of QWidget
when not necessary.

Detail: Some widget never release its 'functional' child, such as
ItemDelegate(with parent set to the view) set by QListView.setItemDelegate
and replaced by other delegate later.
Call deleteLater manually will solve this partially.

PyQt4 has the same problem. But it use less memory than PySide. (Tested under
Windows, 5MB)"""
from PySide.QtCore import *
from PySide.QtGui import *


class DummyDelegate(QAbstractItemDelegate):
    def __init__(self, p=None):
        super(DummyDelegate, self).__init__(p)
        self.w = QWidget()

    def paint(self, *args, **kwargs):
        pass

    def sizeHint(self, *args, **kwargs):
        return QSize()

app = QApplication(['a'])
list = QListView()
for _ in range(10000):
    d = DummyDelegate(list)  # here, with list it takes 26MB, and 13MB if pass None
    list.setItemDelegate(d)
    list.setItemDelegate(None)
    del d


app.exec_()
