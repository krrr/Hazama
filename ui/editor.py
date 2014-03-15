# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'editor.ui'
#
# Created: Sat Mar 15 22:37:12 2014
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Editor(object):
    def setupUi(self, Editor):
        Editor.setObjectName("Editor")
        Editor.resize(400, 300)
        Editor.setStyleSheet("QWidget::Editor{background-color: rgb(249, 245, 238);}")
        self.verticalLayout = QtGui.QVBoxLayout(Editor)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.titleeditor = QtGui.QLineEdit(Editor)
        self.titleeditor.setObjectName("titleeditor")
        self.verticalLayout.addWidget(self.titleeditor)
        self.texteditor = NTextEdit(Editor)
        self.texteditor.setObjectName("texteditor")
        self.verticalLayout.addWidget(self.texteditor)
        spacerItem = QtGui.QSpacerItem(30, 4, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setContentsMargins(20, -1, 20, -1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.tageditor = QtGui.QLineEdit(Editor)
        self.tageditor.setObjectName("tageditor")
        self.horizontalLayout_2.addWidget(self.tageditor)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.timelabel = QtGui.QLabel(Editor)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.timelabel.sizePolicy().hasHeightForWidth())
        self.timelabel.setSizePolicy(sizePolicy)
        self.timelabel.setText("")
        self.timelabel.setObjectName("timelabel")
        self.horizontalLayout.addWidget(self.timelabel)
        self.box = QtGui.QDialogButtonBox(Editor)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.box.sizePolicy().hasHeightForWidth())
        self.box.setSizePolicy(sizePolicy)
        self.box.setOrientation(QtCore.Qt.Horizontal)
        self.box.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Save)
        self.box.setCenterButtons(False)
        self.box.setObjectName("box")
        self.horizontalLayout.addWidget(self.box)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Editor)
        QtCore.QObject.connect(self.box, QtCore.SIGNAL("rejected()"), Editor.closeNoSave)
        QtCore.QObject.connect(self.box, QtCore.SIGNAL("accepted()"), Editor.close)
        QtCore.QMetaObject.connectSlotsByName(Editor)

    def retranslateUi(self, Editor):
        Editor.setWindowTitle(QtGui.QApplication.translate("Editor", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.tageditor.setPlaceholderText(QtGui.QApplication.translate("Editor", "Tags separated by space", None, QtGui.QApplication.UnicodeUTF8))

from .customwidgets import NTextEdit

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Editor = QtGui.QWidget()
    ui = Ui_Editor()
    ui.setupUi(Editor)
    Editor.show()
    sys.exit(app.exec_())

