from PyQt5 import QtCore, QtGui, QtWidgets
import sys

class TrackingDock(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        self.methods = ["nearest_neigbour"]
        super().__init__(parent)

        # init view and callbacks
        self.initView()
        self._connectOwnButtons()

    def initView(self):
        self.setWindowTitle("Cluster tracking")
        self.setFeatures(super().NoDockWidgetFeatures)
        self.setAutoFillBackground(False)
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        # TODO: add options for allowed docking sides, max size, edge outline color

        # set central widget and main layout
        centralWidget = QtWidgets.QWidget()
        centralWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.setWidget(centralWidget)
        mainLayoutV = QtWidgets.QVBoxLayout(centralWidget)

        # toggle button here
        self.enableProcessing = QtWidgets.QCheckBox("Enable cluster tracking")
        mainLayoutV.addWidget(self.enableProcessing)

        # group box 2 - background subtractor
        self.groupBox = QtWidgets.QGroupBox("Tracking options")
        self.groupBox.setEnabled(False)
        mainLayoutV.addWidget(self.groupBox)
        groupLayoutV = QtWidgets.QVBoxLayout(self.groupBox)

        #
        layout = QtWidgets.QHBoxLayout()
        self.method = QtWidgets.QComboBox()
        [self.method.addItem(i) for i in self.methods] # ,"kalman filter"
        layout.addWidget(QtWidgets.QLabel("method:"))
        layout.addWidget(self.method)
        layout.addItem(QtWidgets.QSpacerItem(40, 20,
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        groupLayoutV.addLayout(layout)

        self.method_container_layout = QtWidgets.QStackedLayout()
        groupLayoutV.addLayout(self.method_container_layout)

        # trackers
        self.method_forms = []
        # NearestNeigHbour cluster tracking
        widget = NearestNeighbourForm()
        self.method_container_layout.addWidget(widget)
        self.method_forms.append(widget)

        # KalmanFilter cluster tracking
        #widget = KalmanFilterForm()
        #self.method_container_layout.addWidget(widget)
        #self.method_forms.append(widget)

        #h_layout = QtWidgets.QHBoxLayout()
        #h_layout.addItem(QtWidgets.QSpacerItem(
            #40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        #self.previewButton = QtWidgets.QCheckBox("Display tracks")
        #h_layout.addWidget(self.previewButton)
        #mainLayoutV.addLayout(h_layout)
        
        # apply button
        applyLayoutH = QtWidgets.QHBoxLayout()
        applyLayoutH.addItem(QtWidgets.QSpacerItem(40, 20,
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        self.applyButton = QtWidgets.QPushButton("Apply")
        applyLayoutH.addWidget(self.applyButton)
        mainLayoutV.addLayout(applyLayoutH)

        # bottom spacer 
        mainLayoutV.addItem(QtWidgets.QSpacerItem(20, 40, 
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

    def set_from_config(self, method, params):
        self.enableProcessing.setChecked(True)
        idx = self.methods.index(method)
        self.method.setCurrentIndex(idx)
        self.method_forms[idx].set_from_config(**params)

    def reset(self):
        self.enableProcessing.setChecked(False)
        self.method.setCurrentIndex(0)
        self.method_forms[0].reset()

    def _connectOwnButtons(self):
        self.method.currentIndexChanged[int].connect(self.comboOptionChanged)
        self.enableProcessing.toggled.connect(self.toggleProcessing)

    def getSettings(self):
        idx = self.method_container_layout.currentIndex()
        out = {
            "method": self.method.currentText(),
            "params": self.method_forms[idx].getState()
        }
        return out

    def comboOptionChanged(self, idx):
        self.method_container_layout.setCurrentIndex(idx)

    def toggleProcessing(self):
        state = self.enableProcessing.isChecked()
        self.groupBox.setEnabled(state)

class MethodForm(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inputs = {}
        self.initView()

    def initView():
        pass

    def getState(self):
        state = {}
        for k, v in self.inputs.items():
            if isinstance(v["widget"], QtWidgets.QComboBox):
                state[k] = v["widget"].currentText()
            else:
                state[k] = v["widget"].value()
        return state

class NearestNeighbourForm(MethodForm):
    def __init__(self, parent=None):
        super().__init__(parent)

    def initView(self):
        # override init view
        h_layout = QtWidgets.QHBoxLayout(self)
        # create dictionary with names labels and widgets
        self.inputs["max_missing"] = {"label":"max missing:","widget": QtWidgets.QSpinBox()}
        self.inputs["max_missing"]["widget"].setRange(1, 50)
        self.inputs["max_missing"]["widget"].setValue(3)

        f_layout = QtWidgets.QFormLayout()
        h_layout.addLayout(f_layout)
        for k, v in self.inputs.items():
            f_layout.addRow(QtWidgets.QLabel(v["label"]), v["widget"])
        
        spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum)
        h_layout.addItem(spacer)

    def set_from_config(self, max_missing=3):
        self.inputs["max_missing"]["widget"].setValue(max_missing)

    def reset(self):
        self.inputs["max_missing"]["widget"].setValue(3)

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

    # config testing
    hlayout = QtWidgets.QHBoxLayout()
    mainLayout.addLayout(hlayout)
    get_config = QtWidgets.QPushButton("get config")
    hlayout.addWidget(get_config)
    reset_config = QtWidgets.QPushButton("reset config")
    hlayout.addWidget(reset_config)
    set_config = QtWidgets.QPushButton("set config")
    hlayout.addWidget(set_config)

    dock = TrackingDock(parent=win)
    def test_get_config():
        print(dock.getSettings())

    def test_set_config():
        settings = {
            "method": "nearest_neigbour",
            "params": {
                "max_missing": 1
            }
        }
        dock.set_from_config(settings["method"], settings["params"])
    # connect
    reset_config.clicked.connect(dock.reset)
    get_config.clicked.connect(test_get_config)
    set_config.clicked.connect(test_set_config)

    win.addDockWidget(QtCore.Qt.DockWidgetArea(2), dock)
    win.show()
    sys.exit(app.exec_())

