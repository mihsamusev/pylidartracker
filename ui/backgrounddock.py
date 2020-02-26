from PyQt5 import QtCore, QtGui, QtWidgets

class BackgroundDock(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loadedFile = ""
        self.initView()

        # connect signals
        self.connectOwnButtons()
        self.toggleLoading()
        self.toggleExtraction()
        self.allowBgSubtraction(False)

    def initView(self):
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
        self.loadBackground.setChecked(True)
        groupLayoutV1.addWidget(self.loadBackground)

        # load button
        loadLayoutH1 = QtWidgets.QHBoxLayout()
        self.loadButton = QtWidgets.QPushButton("Load")
        loadLayoutH1.addWidget(self.loadButton)
        self.loadLabel = QtWidgets.QLabel("Background not loaded")
        loadLayoutH1.addWidget(self.loadLabel)
        spacer = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        loadLayoutH1.addItem(spacer)
        groupLayoutV1.addLayout(loadLayoutH1)

        # gb1 - extract
        self.extractBackground = QtWidgets.QRadioButton("Extract background")
        self.extractBackground.setChecked(False)
        groupLayoutV1.addWidget(self.extractBackground)

        # percentile
        extractLayoutG1 = QtWidgets.QGridLayout()
        self.percentileLabel = QtWidgets.QLabel("Percentile")
        extractLayoutG1.addWidget(self.percentileLabel, 0, 0)
        self.percentileBox = QtWidgets.QDoubleSpinBox()
        self.percentileBox.setValue(0.7)
        self.percentileBox.setRange(0.0, 1.0)
        self.percentileBox.setSingleStep(0.1)
        extractLayoutG1.addWidget(self.percentileBox, 0, 1)

        # nonzero
        self.nonzeroLabel = QtWidgets.QLabel("Non zeros percent")
        extractLayoutG1.addWidget(self.nonzeroLabel, 1, 0)
        self.nonzeroBox = QtWidgets.QDoubleSpinBox()
        self.nonzeroBox.setValue(0.8)
        self.nonzeroBox.setRange(0.0, 1.0)
        self.nonzeroBox.setSingleStep(0.1)
        extractLayoutG1.addWidget(self.nonzeroBox, 1, 1)
        
        # nframes
        self.nFramesLabel = QtWidgets.QLabel("Frame count")
        extractLayoutG1.addWidget(self.nFramesLabel, 2, 0)
        self.nFramesBox = QtWidgets.QSpinBox()
        self.nFramesBox.setValue(50)
        extractLayoutG1.addWidget(self.nFramesBox, 2, 1)

        extractLayoutH2 = QtWidgets.QHBoxLayout()
        extractLayoutH2.addLayout(extractLayoutG1)
        spacer = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        extractLayoutH2.addItem(spacer)
        groupLayoutV1.addLayout(extractLayoutH2)

        # extract button
        extractLayoutH3 = QtWidgets.QHBoxLayout()
        self.extractButton = QtWidgets.QPushButton("Extract")
        extractLayoutH3.addWidget(self.extractButton)
        self.extractedLabel = QtWidgets.QLabel("Background not extracted")
        extractLayoutH3.addWidget(self.extractedLabel)
        spacer = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        extractLayoutH3.addItem(spacer)
        groupLayoutV1.addLayout(extractLayoutH3)

        extractLayoutH3 = QtWidgets.QHBoxLayout()
        self.saveButton = QtWidgets.QPushButton("Save")
        extractLayoutH3.addWidget(self.saveButton)
        self.savedLabel = QtWidgets.QLabel("Background not saved")
        extractLayoutH3.addWidget(self.savedLabel)
        spacer = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        extractLayoutH3.addItem(spacer)
        groupLayoutV1.addLayout(extractLayoutH3)

        # preview / save
        extractLayoutH4 = QtWidgets.QHBoxLayout()
        spacer = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        extractLayoutH4.addItem(spacer)
        self.previewButton = QtWidgets.QPushButton("Preview")
        extractLayoutH4.addWidget(self.previewButton)
        groupLayoutV1.addLayout(extractLayoutH4)

        # group box 2 - background subtractor
        self.groupBox2 = QtWidgets.QGroupBox()
        self.groupBox2.setTitle("Background subtractor")
        self.groupBox2.setEnabled(False)
        mainLayoutV.addWidget(self.groupBox2)
        groupLayoutV2 = QtWidgets.QVBoxLayout(self.groupBox2)

        # percentile
        subtractLayoutH1 = QtWidgets.QHBoxLayout()
        self.radiusLabel = QtWidgets.QLabel("KD-tree search radius")
        subtractLayoutH1.addWidget(self.radiusLabel)
        self.radiusBox = QtWidgets.QDoubleSpinBox()
        self.radiusBox.setValue(0.2)
        self.radiusBox.setSingleStep(0.1)
        subtractLayoutH1.addWidget(self.radiusBox)
        spacer = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        subtractLayoutH1.addItem(spacer)
        groupLayoutV2.addLayout(subtractLayoutH1)

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

    def set_from_config(self, **kwargs):
        self.enableSubtraction.setChecked(True)

    def reset(self):
        self.enableSubtraction.setChecked(False)

    def connectOwnButtons(self):
        self.enableSubtraction.stateChanged.connect(self.checkSubtraction)
        self.loadBackground.toggled.connect(self.toggleLoading)
        self.extractBackground.toggled.connect(self.toggleExtraction)
        self.loadButton.clicked.connect(self.getPCDDialog)
        self.saveButton.clicked.connect(self.setPCDDialog)

    def checkSubtraction(self):
        state = self.enableSubtraction.isChecked()
        self.groupBox1.setEnabled(state)
        self.groupBox2.setEnabled(state)

    def toggleLoading(self):
        state = self.loadBackground.isChecked()
        self.loadButton.setEnabled(state)
        self.loadLabel.setEnabled(state)

    def toggleExtraction(self):
        state = self.extractBackground.isChecked()
        self.percentileLabel.setEnabled(state)
        self.percentileBox.setEnabled(state)
        self.nonzeroLabel.setEnabled(state)
        self.nonzeroBox.setEnabled(state)
        self.nFramesLabel.setEnabled(state)
        self.nFramesBox.setEnabled(state)
        self.extractButton.setEnabled(state)
        self.saveButton.setEnabled(state)
        self.extractedLabel.setEnabled(state)
        self.savedLabel.setEnabled(state)

    def allowBgSubtraction(self, state):
        self.radiusBox.setEnabled(state)
        self.radiusLabel.setEnabled(state)
        self.applyButton.setEnabled(state)

    def getPCDDialog(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open File','',"PCD Files (*.pcd)")
        self.loadedFile = fname[0]
        print("[DEBUG] ",fname[0])

    def setPCDDialog(self):
        fname = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save File','',"JSON Files (*.pcd)")
        return fname[0]

    def getSettings(self):
        settings = {
            "subtract": self.enableSubtraction.isChecked(),
            "method": "kd-tree",
            "params": {
                "search_radius": self.radiusBox.value()
                },
            "background": {
                "path": self.loadedFile,
                "method": "range_image",
                "params": {
                    "percentile": self.percentileBox.value(),
                    "non_zero": self.nonzeroBox.value(),
                    "n_frames": self.nFramesBox.value()
                }
            }
        }
        return settings

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
