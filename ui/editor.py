# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'editor.ui'
#
# Created: Wed Mar 19 12:54:00 2014
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
        self.titleEditor = QtGui.QLineEdit(Editor)
        self.titleEditor.setObjectName("titleEditor")
        self.verticalLayout.addWidget(self.titleEditor)
        self.textEditor = NTextEdit(Editor)
        self.textEditor.setObjectName("textEditor")
        self.verticalLayout.addWidget(self.textEditor)
        spacerItem = QtGui.QSpacerItem(30, 4, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setContentsMargins(20, -1, 20, -1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.tagEditor = QtGui.QLineEdit(Editor)
        self.tagEditor.setObjectName("tagEditor")
        self.horizontalLayout_2.addWidget(self.tagEditor)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.dtBtn = QtGui.QToolButton(Editor)
        self.dtBtn.setStyleSheet("QToolButton {border: none;}")
        self.dtBtn.setObjectName("dtBtn")
        self.horizontalLayout.addWidget(self.dtBtn)
        self.dtLabel = QtGui.QLabel(Editor)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dtLabel.sizePolicy().hasHeightForWidth())
        self.dtLabel.setSizePolicy(sizePolicy)
        self.dtLabel.setStyleSheet("color: rgb(80, 80, 80);")
        self.dtLabel.setText("")
        self.dtLabel.setObjectName("dtLabel")
        self.horizontalLayout.addWidget(self.dtLabel)
        self.box = QtGui.QDialogButtonBox(Editor)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
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
        QtCore.QObject.connect(self.tagEditor, QtCore.SIGNAL("textChanged(QString)"), Editor.updateTagEditorFont)
        QtCore.QMetaObject.connectSlotsByName(Editor)

    def retranslateUi(self, Editor):
        self.tagEditor.setPlaceholderText(QtGui.QApplication.translate("Editor", "Tags separated by space", None, QtGui.QApplication.UnicodeUTF8))

from .customwidgets import NTextEdit

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Editor = QtGui.QWidget()
    ui = Ui_Editor()
    ui.setupUi(Editor)
    Editor.show()
    sys.exit(app.exec_())

