from PyQt5 import QtCore, QtGui, QtWidgets
from .xytable import XYTable

class ClippingDock(QtWidgets.QDockWidget):
    valueChanged = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        # data
        self.table = None
        self._zMin = -1.0
        self._zMax = 1.0
        self._range = [-1.0, 1.0]
        self._data = [[0.0, 0.0]]

        # init view and callbacks
        self.initView()
        self._connectOwn()

    def initView(self):
        self.setWindowTitle("Data clipping")
        self.setFeatures(super().NoDockWidgetFeatures)
        self.setAutoFillBackground(False)
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        # TODO: add options for allowed docking sides, max size, edge outline color
        
        # set central widget and main layout
        self.centralWidget = QtWidgets.QWidget()
        self.centralWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.setWidget(self.centralWidget)
        self.mainLayoutV = QtWidgets.QVBoxLayout(self.centralWidget)

        # toggle button here
        self.enableCropping = QtWidgets.QCheckBox("Enable data cropping")
        self.mainLayoutV.addWidget(self.enableCropping)

        # group box 1 - coordinate syste
        self.groupBox1 = QtWidgets.QGroupBox()
        self.groupBox1.setTitle("Crop box definition")
        self.groupBox1.setEnabled(False)
        self.mainLayoutV.addWidget(self.groupBox1)
        self.groupLayoutV1 = QtWidgets.QVBoxLayout(self.groupBox1)

        # z range method
        self.inputLayoutH1 = QtWidgets.QHBoxLayout()
        rangeLabel1 = QtWidgets.QLabel("Z range between")
        self.inputLayoutH1.addWidget(rangeLabel1)

        self.zMinBox = QtWidgets.QDoubleSpinBox()
        self.zMinBox.setRange(-200.0, 200.0)
        self.zMinBox.setValue(self._zMin)
        self.inputLayoutH1.addWidget(self.zMinBox)
        self.zMaxBox = QtWidgets.QDoubleSpinBox()
        self.zMaxBox.setRange(-200.0, 200.0)
        self.zMaxBox.setValue(self._zMax)
        self.inputLayoutH1.addWidget(self.zMaxBox)

        zSpacerH1 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.inputLayoutH1.addItem(zSpacerH1)
        self.groupLayoutV1.addLayout(self.inputLayoutH1)

        # label
        tableLabel = QtWidgets.QLabel("XY polygon")
        self.groupLayoutV1.addWidget(tableLabel)

        # table and buttons
        inputLayoutH2 = QtWidgets.QHBoxLayout()

        # table itself
        self.table = XYTable()
        inputLayoutH2.addWidget(self.table)

        inputLayoutV2 = QtWidgets.QVBoxLayout()
        inputLayoutH2.addLayout(inputLayoutV2)

        self.addRowsAboveBtn = QtWidgets.QPushButton("Add row above")
        self.addRowsBelowBtn = QtWidgets.QPushButton("Add row below")
        self.deleteRowsBtn = QtWidgets.QPushButton("Delete row(s)")

        # adders
        self.addxBtn = QtWidgets.QPushButton("Move all X")
        self.addxDSB = QtWidgets.QDoubleSpinBox()
        self.addxDSB.setRange(-20,20)
        self.addxDSB.setValue(1.0)
        addx_layout = QtWidgets.QHBoxLayout()
        addx_layout.addWidget(self.addxBtn)
        addx_layout.addWidget(self.addxDSB)

        self.addyBtn = QtWidgets.QPushButton("Move all Y")
        self.addyDSB = QtWidgets.QDoubleSpinBox()
        self.addyDSB.setRange(-20,20)
        self.addyDSB.setValue(1.0)
        addy_layout = QtWidgets.QHBoxLayout()
        addy_layout.addWidget(self.addyBtn)
        addy_layout.addWidget(self.addyDSB)

        inputLayoutV2.addWidget(self.addRowsAboveBtn)
        inputLayoutV2.addWidget(self.addRowsBelowBtn)
        inputLayoutV2.addWidget(self.deleteRowsBtn)
        inputLayoutV2.addLayout(addx_layout)
        inputLayoutV2.addLayout(addy_layout)
        
        
        buttonSpacerV = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Expanding)
        inputLayoutV2.addItem(buttonSpacerV)

        tableSpacerH = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        inputLayoutH2.addItem(tableSpacerH)

        self.groupLayoutV1.addLayout(inputLayoutH2)


        # togles for display and inverse
        self.displayCropBox = QtWidgets.QCheckBox("Display crop box")
        self.inverseCropping = QtWidgets.QCheckBox(
            "Inverse cropping (keep points outside range)")
        self.groupLayoutV1.addWidget(self.displayCropBox)
        self.groupLayoutV1.addWidget(self.inverseCropping)

        # apply button
        self.applyLayoutH = QtWidgets.QHBoxLayout()
        self.applySpacerH = QtWidgets.QSpacerItem(40, 20, 
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.applyLayoutH.addItem(self.applySpacerH)
        self.applyButton = QtWidgets.QPushButton("Apply")
        self.applyLayoutH.addWidget(self.applyButton)
        self.mainLayoutV.addLayout(self.applyLayoutH)
        self.bottomSpacerV = QtWidgets.QSpacerItem(20, 40, 
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.mainLayoutV.addItem(self.bottomSpacerV)

    def set_from_config(self, polygon, z_range, inverse):
        self.enableCropping.setChecked(True)
        self.displayCropBox.setChecked(False)
                
        self.table.setData(polygon)
        self.zMinBox.setValue(z_range[0])
        self.zMaxBox.setValue(z_range[1])
        self.addxDSB.setValue(1.0)
        self.addyDSB.setValue(1.0)
        self.displayCropBox.setChecked(True)
        self.inverseCropping.setChecked(inverse)

    def reset(self):
        self.enableCropping.setChecked(False)
        self.displayCropBox.setChecked(False)

        self.table.setData(None)
        self.zMinBox.setValue(-1.0)
        self.zMaxBox.setValue(1.0)
        self.addxDSB.setValue(1.0)
        self.addyDSB.setValue(1.0)
        self.inverseCropping.setChecked(False)

    def _connectOwn(self):
        # enable / disable
        self.enableCropping.stateChanged.connect(self._toggleInput)

        # buttons and table
        self.addRowsAboveBtn.clicked.connect(self.table._addabove)
        self.addRowsBelowBtn.clicked.connect(self.table._addbelow)
        self.deleteRowsBtn.clicked.connect(self.table._removerow)
        
        self.zMinBox.valueChanged.connect(self._updatezmin)
        self.zMaxBox.valueChanged.connect(self._updatezmax)
        self.table.valueChanged.connect(self._updateData)
        self.displayCropBox.stateChanged.connect(self._updateDisplay)
        self.addxBtn.clicked.connect(self.addX)
        self.addyBtn.clicked.connect(self.addY)

    def _updateDisplay(self):
        self.valueChanged.emit()

    def _toggleInput(self):
        if self.enableCropping.isChecked():
            self.groupBox1.setEnabled(True)
        else:
            self.groupBox1.setEnabled(False)

    def _updatezmax(self, d):
        self._zMax = d
        self._updateRange()

    def _updatezmin(self, d):
        self._zMin = d
        self._updateRange()

    def _updateRange(self):
        self._range = [self._zMin, self._zMax]
        if self._zMin > self._zMax:
            self._range.reverse()
        self.valueChanged.emit()

    def _updateData(self):
        self._data = self.table.getData()
        self.valueChanged.emit()

    def addX(self):
        value = self.addxDSB.value()
        self.table._add_x(value)

    def addY(self):
        value = self.addyDSB.value()
        self.table._add_y(value)

    def getSettings(self):
        settings = {
            "transform": self.enableCropping.isChecked(),
            "display": self.displayCropBox.isChecked(),
            "params": {
                "z_range": self._range,
                "polygon": self._data,
                "inverse": self.inverseCropping.isChecked()
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

    dock = ClippingDock(parent=win)
    win.addDockWidget(QtCore.Qt.DockWidgetArea(2), dock)

    win.show()
    sys.exit(app.exec_())