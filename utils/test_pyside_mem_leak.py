"""Do not pass parent to some object that isn't sub-class of QWidget
when not necessary.

Detail: Some widget never release its non widget child, such as
ItemDelegate (with parent set to the view) set by QListView.setItemDelegate
and replaced by other delegate later.
Call deleteLater manually will solve this partially.

PyQt4 has the same problem. But it use less memory than PySide. (Tested on
Windows, 5MB lesser)"""
from PySide.QtCore import *
from PySide.QtGui import *


class DummyDelegate(QAbstractItemDelegate):
    def paint(self, *args, **kwargs):
        pass

    def sizeHint(self, *args, **kwargs):
        return QSize()


app = QApplication(['a'])
list = QListView()
for _ in range(100000):
    d = DummyDelegate()  # here, with list it takes 100+MB, and 16MB if pass None
    list.setItemDelegate(d)
    list.setItemDelegate(None)
    del d


print('app_exec')
app.exec_()
