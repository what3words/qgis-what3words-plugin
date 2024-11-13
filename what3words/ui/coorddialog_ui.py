# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'what3words/ui/coorddialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_discoverToWhat3words(object):
    def setupUi(self, discoverToWhat3words):
        discoverToWhat3words.setObjectName("discoverToWhat3words")
        discoverToWhat3words.resize(436, 300)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(discoverToWhat3words.sizePolicy().hasHeightForWidth())
        discoverToWhat3words.setSizePolicy(sizePolicy)
        discoverToWhat3words.setMinimumSize(QtCore.QSize(436, 300))
        discoverToWhat3words.setFloating(True)
        discoverToWhat3words.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)
        self.dockWidgetContents = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dockWidgetContents.sizePolicy().hasHeightForWidth())
        self.dockWidgetContents.setSizePolicy(sizePolicy)
        self.dockWidgetContents.setMinimumSize(QtCore.QSize(436, 285))
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout.setObjectName("verticalLayout")
        self.topButtons = QtWidgets.QHBoxLayout()
        self.topButtons.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.topButtons.setObjectName("topButtons")
        self.viewGridButton = QtWidgets.QToolButton(self.dockWidgetContents)
        self.viewGridButton.setMinimumSize(QtCore.QSize(30, 30))
        self.viewGridButton.setObjectName("viewGridButton")
        self.topButtons.addWidget(self.viewGridButton)
        self.openMapsiteButton = QtWidgets.QToolButton(self.dockWidgetContents)
        self.openMapsiteButton.setMinimumSize(QtCore.QSize(30, 30))
        self.openMapsiteButton.setAutoRaise(False)
        self.openMapsiteButton.setArrowType(QtCore.Qt.NoArrow)
        self.openMapsiteButton.setObjectName("openMapsiteButton")
        self.topButtons.addWidget(self.openMapsiteButton)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.topButtons.addItem(spacerItem)
        self.saveToFileButton = QtWidgets.QToolButton(self.dockWidgetContents)
        self.saveToFileButton.setMinimumSize(QtCore.QSize(30, 30))
        self.saveToFileButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.saveToFileButton.setAutoRaise(False)
        self.saveToFileButton.setObjectName("saveToFileButton")
        self.topButtons.addWidget(self.saveToFileButton)
        self.createLayerButton = QtWidgets.QToolButton(self.dockWidgetContents)
        self.createLayerButton.setMinimumSize(QtCore.QSize(30, 30))
        self.createLayerButton.setObjectName("createLayerButton")
        self.topButtons.addWidget(self.createLayerButton)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.topButtons.addItem(spacerItem1)
        self.deleteSelectedButton = QtWidgets.QToolButton(self.dockWidgetContents)
        self.deleteSelectedButton.setMinimumSize(QtCore.QSize(30, 30))
        self.deleteSelectedButton.setObjectName("deleteSelectedButton")
        self.topButtons.addWidget(self.deleteSelectedButton)
        self.clearAll = QtWidgets.QToolButton(self.dockWidgetContents)
        self.clearAll.setMinimumSize(QtCore.QSize(30, 30))
        self.clearAll.setObjectName("clearAll")
        self.topButtons.addWidget(self.clearAll)
        self.settingsButton = QtWidgets.QToolButton(self.dockWidgetContents)
        self.settingsButton.setMinimumSize(QtCore.QSize(30, 30))
        self.settingsButton.setObjectName("settingsButton")
        self.topButtons.addWidget(self.settingsButton)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.topButtons.addItem(spacerItem2)
        self.verticalLayout.addLayout(self.topButtons)
        self.w3wLabel = QtWidgets.QLabel(self.dockWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.w3wLabel.sizePolicy().hasHeightForWidth())
        self.w3wLabel.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Microsoft Sans Serif")
        font.setPointSize(14)
        self.w3wLabel.setFont(font)
        self.w3wLabel.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
        self.w3wLabel.setToolTipDuration(1)
        self.w3wLabel.setObjectName("w3wLabel")
        self.verticalLayout.addWidget(self.w3wLabel)
        self.inputField = QtWidgets.QGridLayout()
        self.inputField.setObjectName("inputField")
        self.addLineEdit = QtWidgets.QLineEdit(self.dockWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addLineEdit.sizePolicy().hasHeightForWidth())
        self.addLineEdit.setSizePolicy(sizePolicy)
        self.addLineEdit.setMinimumSize(QtCore.QSize(0, 30))
        self.addLineEdit.setMaximumSize(QtCore.QSize(16777215, 30))
        font = QtGui.QFont()
        font.setFamily("Microsoft Sans Serif")
        font.setPointSize(14)
        self.addLineEdit.setFont(font)
        self.addLineEdit.setText("")
        self.addLineEdit.setFrame(True)
        self.addLineEdit.setClearButtonEnabled(True)
        self.addLineEdit.setObjectName("addLineEdit")
        self.inputField.addWidget(self.addLineEdit, 0, 0, 1, 1)
        self.w3wCaptureButton = QtWidgets.QToolButton(self.dockWidgetContents)
        self.w3wCaptureButton.setMinimumSize(QtCore.QSize(30, 30))
        self.w3wCaptureButton.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.w3wCaptureButton.setCheckable(True)
        self.w3wCaptureButton.setObjectName("w3wCaptureButton")
        self.inputField.addWidget(self.w3wCaptureButton, 0, 1, 1, 1)
        self.clipToExtentButton = QtWidgets.QToolButton(self.dockWidgetContents)
        self.clipToExtentButton.setMinimumSize(QtCore.QSize(30, 30))
        self.clipToExtentButton.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
        self.clipToExtentButton.setObjectName("clipToExtentButton")
        self.inputField.addWidget(self.clipToExtentButton, 0, 2, 1, 1)
        self.verticalLayout.addLayout(self.inputField)
        self.tableWidget = QtWidgets.QTableWidget(self.dockWidgetContents)
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.verticalLayout.addWidget(self.tableWidget)
        self.bottomButtons = QtWidgets.QHBoxLayout()
        self.bottomButtons.setObjectName("bottomButtons")
        self.showAllMarkersCheckBox = QtWidgets.QCheckBox(self.dockWidgetContents)
        self.showAllMarkersCheckBox.setObjectName("showAllMarkersCheckBox")
        self.bottomButtons.addWidget(self.showAllMarkersCheckBox)
        self.clearMarkersButton = QtWidgets.QToolButton(self.dockWidgetContents)
        self.clearMarkersButton.setObjectName("clearMarkersButton")
        self.bottomButtons.addWidget(self.clearMarkersButton)
        self.verticalLayout.addLayout(self.bottomButtons)
        discoverToWhat3words.setWidget(self.dockWidgetContents)

        self.retranslateUi(discoverToWhat3words)
        QtCore.QMetaObject.connectSlotsByName(discoverToWhat3words)

    def retranslateUi(self, discoverToWhat3words):
        _translate = QtCore.QCoreApplication.translate
        discoverToWhat3words.setToolTip(_translate("discoverToWhat3words", "Discover what3words address"))
        discoverToWhat3words.setWindowTitle(_translate("discoverToWhat3words", "Discover what3words address"))
        self.dockWidgetContents.setToolTip(_translate("discoverToWhat3words", "what3words address Tools"))
        self.viewGridButton.setToolTip(_translate("discoverToWhat3words", "View Grid"))
        self.viewGridButton.setText(_translate("discoverToWhat3words", "..."))
        self.openMapsiteButton.setToolTip(_translate("discoverToWhat3words", "Show in what3words mapsite"))
        self.openMapsiteButton.setText(_translate("discoverToWhat3words", "..."))
        self.saveToFileButton.setToolTip(_translate("discoverToWhat3words", "Save to File"))
        self.saveToFileButton.setText(_translate("discoverToWhat3words", "..."))
        self.createLayerButton.setToolTip(_translate("discoverToWhat3words", "Create Vector Layer From what3words List"))
        self.createLayerButton.setText(_translate("discoverToWhat3words", "..."))
        self.deleteSelectedButton.setToolTip(_translate("discoverToWhat3words", "Delete selected what3words from the table"))
        self.deleteSelectedButton.setText(_translate("discoverToWhat3words", "..."))
        self.clearAll.setToolTip(_translate("discoverToWhat3words", "Clear All what3words from List"))
        self.clearAll.setText(_translate("discoverToWhat3words", "..."))
        self.settingsButton.setToolTip(_translate("discoverToWhat3words", "Settings"))
        self.settingsButton.setText(_translate("discoverToWhat3words", "..."))
        self.w3wLabel.setToolTip(_translate("discoverToWhat3words", "Enter what3words address"))
        self.w3wLabel.setText(_translate("discoverToWhat3words", "Enter what3words address"))
        self.addLineEdit.setToolTip(_translate("discoverToWhat3words", "Enter what3words address here e.g.  ///index.home.raft"))
        self.addLineEdit.setPlaceholderText(_translate("discoverToWhat3words", "e.g. ///index.home.raft"))
        self.w3wCaptureButton.setToolTip(_translate("discoverToWhat3words", "Capture what3words address by clicking on map"))
        self.w3wCaptureButton.setText(_translate("discoverToWhat3words", "..."))
        self.clipToExtentButton.setToolTip(_translate("discoverToWhat3words", "Clip to Extent"))
        self.clipToExtentButton.setText(_translate("discoverToWhat3words", "..."))
        self.tableWidget.setToolTip(_translate("discoverToWhat3words", "List of what3words address"))
        self.showAllMarkersCheckBox.setToolTip(_translate("discoverToWhat3words", "Show All Markers"))
        self.showAllMarkersCheckBox.setText(_translate("discoverToWhat3words", "Show All Markers"))
        self.clearMarkersButton.setToolTip(_translate("discoverToWhat3words", "Clear Markers"))
        self.clearMarkersButton.setText(_translate("discoverToWhat3words", "..."))
