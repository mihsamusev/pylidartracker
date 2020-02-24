from PyQt5 import QtCore, QtGui, QtWidgets

class BackgroundDock(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Background subtraction")
        self.setAutoFillBackground(False)
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        # TODO: add options for allowed docking sides, max size, edge outline color
        
        # set central widget and main layout
        centralWidget = QtWidgets.QWidget()
        self.setWidget(centralWidget)
        mainLayoutV = QtWidgets.QVBoxLayout(centralWidget)

        # toggle button here
        self.enableSubtraction = QtWidgets.QCheckBox("Enable background subtraction")
        mainLayoutV.addWidget(self.enableSubtraction)

        # group box 1 - background pc
        self.groupBox1 = QtWidgets.QGroupBox()
        self.groupBox1.setTitle("Background point cloud")
        self.groupBox1.setEnabled(False)
        mainLayoutV.addWidget(self.groupBox1)
        groupLayoutV1 = QtWidgets.QVBoxLayout(self.groupBox1)

        # gb1 - load
        self.loadBackground = QtWidgets.QRadioButton("Load background")
        self.loadBackground.setChecked(False)#############################
        groupLayoutV1.addWidget(self.loadBackground)

        # z range method
        self.loadLayoutH1 = QtWidgets.QHBoxLayout()
        self.loadLayoutH1.setEnabled(False)
        self.loadButton = QtWidgets.QPushButton("...")
        self.loadLayoutH1.addWidget(self.loadButton)
        self.loadLabel = QtWidgets.QLabel("Background not loaded")
        self.loadLayoutH1.addWidget(self.loadLabel)
        inputSpacerH1 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.loadLayoutH1.addItem(inputSpacerH1)
        groupLayoutV1.addLayout(self.loadLayoutH1)

        # gb1 - extract
        self.extractBackground = QtWidgets.QRadioButton("Extract background")
        self.extractBackground.setChecked(False)
        groupLayoutV1.addWidget(self.extractBackground)

        # group box 2 - background subtractor
        self.groupBox2 = QtWidgets.QGroupBox()
        self.groupBox2.setTitle("Background subtractor")
        self.groupBox2.setEnabled(False)
        mainLayoutV.addWidget(self.groupBox2)
        groupLayoutV2 = QtWidgets.QVBoxLayout(self.groupBox2)

        # apply button
        applyLayoutH = QtWidgets.QHBoxLayout()
        applySpacerH = QtWidgets.QSpacerItem(40, 20, 
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        applyLayoutH.addItem(applySpacerH)
        self.applyButton = QtWidgets.QPushButton("Apply")
        applyLayoutH.addWidget(self.applyButton)
        groupLayoutV2.addLayout(applyLayoutH)

        # bottom spacer
        bottomSpacerV = QtWidgets.QSpacerItem(20, 40, 
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        mainLayoutV.addItem(bottomSpacerV)

        # connect visual signals
        self.connectOwnButtons()

    def set_from_config(self, **kwargs):
        self.enableSubtraction.setChecked(True)

    def reset(self):
        self.enableSubtraction.setChecked(False)

    def connectOwnButtons(self):
        self.enableSubtraction.stateChanged.connect(self.toggleSubtraction)
        self.loadBackground.toggled.connect(self.toggleLoading)

    def toggleSubtraction(self):
        if self.enableSubtraction.isChecked():
            self.groupBox1.setEnabled(True)
            self.groupBox2.setEnabled(True)
        else:
            self.groupBox1.setEnabled(False)
            self.groupBox2.setEnabled(False)

    def toggleLoading(self):
        if self.loadBackground.isChecked():
            self.loadLayoutH1.setEnabled(True)
        else:
            self.loadLayoutH1.setEnabled(False)

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    win = QtWidgets.QMainWindow()
    win.setWindowTitle("Your favorite app")
    win.resize(800, 600)
    centralWidget = QtWidgets.QWidget(parent=win)
    centralWidget.setMinimumSize(QtCore.QSize(400, 300))
    mainLayout = QtWidgets.QVBoxLayout(centralWidget)
    win.setCentralWidget(centralWidget)
    
    dock = BackgroundDock(parent=win)
    win.addDockWidget(QtCore.Qt.DockWidgetArea(2), dock)
    win.show()
    sys.exit(app.exec_())

