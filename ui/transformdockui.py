from PyQt5 import QtCore, QtGui, QtWidgets

class TransformDock(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Coordinate transformation")
        self.setFeatures(super().NoDockWidgetFeatures)
        self.setAutoFillBackground(False)
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        # TODO: add options for allowed docking sides, max size, edge outline color
        
        # set central widget and main layout
        self.centralWidget = QtWidgets.QWidget()
        self.setWidget(self.centralWidget)
        self.mainLayoutV = QtWidgets.QVBoxLayout(self.centralWidget)

        # toggle button here
        self.enableTransform = QtWidgets.QCheckBox("Enable coordinate transformation")
        self.mainLayoutV.addWidget(self.enableTransform)

        # group box - plane estimation
        self.groupBox = QtWidgets.QGroupBox()
        self.groupBox.setTitle("New XY plane estimation")
        self.groupBox.setEnabled(False)
        self.mainLayoutV.addWidget(self.groupBox)
        self.groupLayoutV = QtWidgets.QVBoxLayout(self.groupBox)

        self.pickStatus = QtWidgets.QLabel("Pick 3 points with right mouse clicks")
        self.groupLayoutV.addWidget(self.pickStatus)

        inputLayoutH = QtWidgets.QHBoxLayout()
        self.pickBtn = QtWidgets.QPushButton("Start point picking")
        self.pickBtn.setCheckable(True)
        inputLayoutH.addWidget(self.pickBtn)

        pickSpacerH = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        inputLayoutH.addItem(pickSpacerH)
        self.groupLayoutV.addLayout(inputLayoutH)

        # table
        self.transformHeader = QtWidgets.QLabel("")
        self.transformHeader.setEnabled(False)
        self.transformResult = QtWidgets.QLabel("")
        self.transformResult.setEnabled(False)
        self.updateResult(None)
        self.groupLayoutV.addWidget(self.transformHeader)
        self.groupLayoutV.addWidget(self.transformResult)

        # apply button
        self.applyLayoutH = QtWidgets.QHBoxLayout()
        self.applySpacerH = QtWidgets.QSpacerItem(40, 20, 
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.applyLayoutH.addItem(self.applySpacerH)
        self.applyButton = QtWidgets.QPushButton("Apply")
        self.applyLayoutH.addWidget(self.applyButton)
        self.mainLayoutV.addLayout(self.applyLayoutH)

        # spacer
        self.bottomSpacerV = QtWidgets.QSpacerItem(20, 40, 
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.mainLayoutV.addItem(self.bottomSpacerV)

        # connect visual signals
        self.connectOwnButtons()

    def set_from_config(self, **kwargs):
        self.enableTransform.setChecked(True)
        self.updateResult(kwargs["normal"], kwargs["intercept"])
        self.enableResults(True)

    def reset(self):
        self.enableTransform.setChecked(False)
        self.updateResult(None)
        self.enableResults(False)

    def connectOwnButtons(self):
        self.enableTransform.stateChanged.connect(self.toggleTransform)

    def toggleTransform(self):
        if self.enableTransform.isChecked():
            self.groupBox.setEnabled(True)
        else:
            self.groupBox.setEnabled(False)

    def _get_result_text(self, normal, intercept):
        return (
            f"nx = {normal[0]:.2f};\n"
            f"ny = {normal[1]:.2f};\n"
            f"nz = {normal[2]:.2f};\n"
            f"offset = {intercept:.2f}\n"
            "(relative to the original CS)")

    def updateResult(self, normal=None, intercept=None):
        """Display calculated values for plane normal and offset"""
        if normal is None or intercept is None:
            self.transformHeader.setText("Plane is not estimated")
            txt = ""
        else:
            self.transformHeader.setText("Plane is estimated:")
            txt = self._get_result_text(normal, intercept)
        self.transformResult.setText(txt)

    def enableResults(self, state):
        self.transformHeader.setEnabled(state)
        self.transformResult.setEnabled(state)

class ExampleController():
    def __init__(self, dock, graphics):
        self.dock = dock
        self.graphics = graphics
        self.dock.pickBtn.toggled.connect(self._allowSelection)
        self.graphics.threePointsPicked.connect(self._countPoints)
        self.dock.enableResults(False)

    def _countPoints(self):
        print("data ready!!! GONN TRANSFORM SHTR")
        print("Gonnna use")
        print(self.graphics.getSelectedPoints())
        self.dock.pickBtn.setChecked(False)

    def _allowSelection(self):
        if self.dock.pickBtn.isChecked():
            self.dock.pickBtn.setText("Stop point picking")
            self.graphics.setSelectionAllowed(True)
            self.graphics.setSelectedVisible(True)
            self.graphics.resetSelected()
            self.dock.enableResults(False)
        else:
            self.dock.pickBtn.setText("Start point picking")
            self.graphics.setSelectionAllowed(False)
            
            if self.graphics.nSelected != 3:
                self.graphics.resetSelected()
            else:
                self.dock.enableResults(True)

if __name__ == '__main__':
    import sys
    from lidargraphicsview import LidarGraphicsView
    import numpy as np

    app = QtWidgets.QApplication(sys.argv)
    win = QtWidgets.QMainWindow()
    win.setWindowTitle("Your favorite app")
    win.resize(800, 600)
    centralWidget = QtWidgets.QWidget(parent=win)
    centralWidget.setMinimumSize(QtCore.QSize(400, 300))
    mainLayout = QtWidgets.QVBoxLayout(centralWidget)
    win.setCentralWidget(centralWidget)

    graphicsView = LidarGraphicsView()
    mainLayout.addWidget(graphicsView)
    
    pts = -0.5 + np.random.rand(500,3)
    graphicsView.setRawPoints(pts)
    graphicsView.draw()
    
    dock = TransformDock(parent=win)
    win.addDockWidget(QtCore.Qt.DockWidgetArea(2), dock)

    ctrl = ExampleController(dock, graphicsView)
    win.show()
    sys.exit(app.exec_())

