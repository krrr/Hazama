# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'configdialog.ui'
#
# Created: Tue Feb 25 16:28:01 2014
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Settings(object):
    def setupUi(self, Settings):
        Settings.setObjectName("Settings")
        Settings.setWindowModality(QtCore.Qt.NonModal)
        Settings.resize(400, 410)
        Settings.setSizeGripEnabled(False)
        Settings.setModal(False)
        self.verticalLayout = QtGui.QVBoxLayout(Settings)
        self.verticalLayout.setContentsMargins(7, 7, 7, 7)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtGui.QTabWidget(Settings)
        self.tabWidget.setTabShape(QtGui.QTabWidget.Rounded)
        self.tabWidget.setDocumentMode(False)
        self.tabWidget.setTabsClosable(False)
        self.tabWidget.setMovable(False)
        self.tabWidget.setObjectName("tabWidget")
        self.general = QtGui.QWidget()
        self.general.setObjectName("general")
        self.verticalLayout_6 = QtGui.QVBoxLayout(self.general)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_2 = QtGui.QLabel(self.general)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_4.addWidget(self.label_2)
        self.langCombo = QtGui.QComboBox(self.general)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.langCombo.sizePolicy().hasHeightForWidth())
        self.langCombo.setSizePolicy(sizePolicy)
        self.langCombo.setObjectName("langCombo")
        self.langCombo.addItem("")
        self.langCombo.addItem("")
        self.langCombo.addItem("")
        self.horizontalLayout_4.addWidget(self.langCombo)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.verticalLayout_6.addLayout(self.horizontalLayout_4)
        self.editorBox = QtGui.QGroupBox(self.general)
        self.editorBox.setObjectName("editorBox")
        self.verticalLayout_7 = QtGui.QVBoxLayout(self.editorBox)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.aindCheck = QtGui.QCheckBox(self.editorBox)
        self.aindCheck.setObjectName("aindCheck")
        self.verticalLayout_7.addWidget(self.aindCheck)
        self.copenCheck = QtGui.QCheckBox(self.editorBox)
        self.copenCheck.setObjectName("copenCheck")
        self.verticalLayout_7.addWidget(self.copenCheck)
        self.verticalLayout_6.addWidget(self.editorBox)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_6.addItem(spacerItem1)
        self.tabWidget.addTab(self.general, "")
        self.nikkichou = QtGui.QWidget()
        self.nikkichou.setObjectName("nikkichou")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.nikkichou)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.bkBox = QtGui.QGroupBox(self.nikkichou)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bkBox.sizePolicy().hasHeightForWidth())
        self.bkBox.setSizePolicy(sizePolicy)
        self.bkBox.setObjectName("bkBox")
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.bkBox)
        self.verticalLayout_4.setSpacing(24)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.bkLabel = QtGui.QLabel(self.bkBox)
        self.bkLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.bkLabel.setObjectName("bkLabel")
        self.verticalLayout_4.addWidget(self.bkLabel)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.bkCheck = QtGui.QCheckBox(self.bkBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bkCheck.sizePolicy().hasHeightForWidth())
        self.bkCheck.setSizePolicy(sizePolicy)
        self.bkCheck.setObjectName("bkCheck")
        self.horizontalLayout.addWidget(self.bkCheck)
        self.rstBtn = QtGui.QPushButton(self.bkBox)
        self.rstBtn.setObjectName("rstBtn")
        self.horizontalLayout.addWidget(self.rstBtn)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.verticalLayout_3.addWidget(self.bkBox)
        self.groupBox_2 = QtGui.QGroupBox(self.nikkichou)
        self.groupBox_2.setFlat(False)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_5 = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_5.setSpacing(24)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.exportLabel = QtGui.QLabel(self.groupBox_2)
        self.exportLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.exportLabel.setObjectName("exportLabel")
        self.verticalLayout_5.addWidget(self.exportLabel)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.exportOption = QtGui.QComboBox(self.groupBox_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.exportOption.sizePolicy().hasHeightForWidth())
        self.exportOption.setSizePolicy(sizePolicy)
        self.exportOption.setFrame(True)
        self.exportOption.setObjectName("exportOption")
        self.exportOption.addItem("")
        self.exportOption.addItem("")
        self.horizontalLayout_3.addWidget(self.exportOption)
        self.exportBtn = QtGui.QPushButton(self.groupBox_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.exportBtn.sizePolicy().hasHeightForWidth())
        self.exportBtn.setSizePolicy(sizePolicy)
        self.exportBtn.setAutoDefault(False)
        self.exportBtn.setObjectName("exportBtn")
        self.horizontalLayout_3.addWidget(self.exportBtn)
        self.verticalLayout_5.addLayout(self.horizontalLayout_3)
        self.verticalLayout_3.addWidget(self.groupBox_2)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem3)
        self.tabWidget.addTab(self.nikkichou, "")
        self.appearance = QtGui.QWidget()
        self.appearance.setObjectName("appearance")
        self.tabWidget.addTab(self.appearance, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtGui.QDialogButtonBox(Settings)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Settings)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Settings.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Settings.reject)
        QtCore.QMetaObject.connectSlotsByName(Settings)

    def retranslateUi(self, Settings):
        Settings.setWindowTitle(QtGui.QApplication.translate("Settings", "Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Settings", "Language:", None, QtGui.QApplication.UnicodeUTF8))
        self.langCombo.setItemText(0, QtGui.QApplication.translate("Settings", "English", None, QtGui.QApplication.UnicodeUTF8))
        self.langCombo.setItemText(1, QtGui.QApplication.translate("Settings", "简体中文", None, QtGui.QApplication.UnicodeUTF8))
        self.langCombo.setItemText(2, QtGui.QApplication.translate("Settings", "日本語", None, QtGui.QApplication.UnicodeUTF8))
        self.editorBox.setTitle(QtGui.QApplication.translate("Settings", "Editor", None, QtGui.QApplication.UnicodeUTF8))
        self.aindCheck.setText(QtGui.QApplication.translate("Settings", "Auto indent", None, QtGui.QApplication.UnicodeUTF8))
        self.copenCheck.setText(QtGui.QApplication.translate("Settings", "Open in the center of main window", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.general), QtGui.QApplication.translate("Settings", "General", None, QtGui.QApplication.UnicodeUTF8))
        self.bkBox.setTitle(QtGui.QApplication.translate("Settings", "Backup", None, QtGui.QApplication.UnicodeUTF8))
        self.bkLabel.setText(QtGui.QApplication.translate("Settings", "Backup every day and keep each one for a week.", None, QtGui.QApplication.UnicodeUTF8))
        self.bkCheck.setText(QtGui.QApplication.translate("Settings", "Enable backup", None, QtGui.QApplication.UnicodeUTF8))
        self.rstBtn.setText(QtGui.QApplication.translate("Settings", "Restore", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("Settings", "Export", None, QtGui.QApplication.UnicodeUTF8))
        self.exportLabel.setText(QtGui.QApplication.translate("Settings", "Export diary to single plain text file or RTF file.", None, QtGui.QApplication.UnicodeUTF8))
        self.exportOption.setItemText(0, QtGui.QApplication.translate("Settings", "All diary", None, QtGui.QApplication.UnicodeUTF8))
        self.exportOption.setItemText(1, QtGui.QApplication.translate("Settings", "Selected diary", None, QtGui.QApplication.UnicodeUTF8))
        self.exportBtn.setText(QtGui.QApplication.translate("Settings", "Save as...", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.nikkichou), QtGui.QApplication.translate("Settings", "Diary", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.appearance), QtGui.QApplication.translate("Settings", "Appearance", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Settings = QtGui.QDialog()
    ui = Ui_Settings()
    ui.setupUi(Settings)
    Settings.show()
    sys.exit(app.exec_())

