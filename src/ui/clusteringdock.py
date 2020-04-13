from PyQt5 import QtCore, QtGui, QtWidgets
import sys

class ClusteringDock(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        self.methods = ["naive","dbscan"]
        super().__init__(parent)

        # init view and callbacks
        self.initView()
        self._connectOwnButtons()

    def initView(self):
        self.setWindowTitle("Clustering")
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
        self.enableProcessing = QtWidgets.QCheckBox("Enable clustering")
        mainLayoutV.addWidget(self.enableProcessing)

        # group box 2 - background subtractor
        self.groupBox = QtWidgets.QGroupBox("Clustering options")
        self.groupBox.setEnabled(False)
        mainLayoutV.addWidget(self.groupBox)
        groupLayoutV = QtWidgets.QVBoxLayout(self.groupBox)

        #
        layout = QtWidgets.QHBoxLayout()
        self.method = QtWidgets.QComboBox()
        [self.method.addItem(i) for i in self.methods]
        layout.addWidget(QtWidgets.QLabel("method:"))
        layout.addWidget(self.method)
        layout.addItem(QtWidgets.QSpacerItem(40, 20,
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        groupLayoutV.addLayout(layout)

        self.method_container_layout = QtWidgets.QStackedLayout()
        groupLayoutV.addLayout(self.method_container_layout)

        # clusters
        self.method_forms = []
        # agglomerative cluster
        widget = AgglomerativeClusteringForm()
        self.method_container_layout.addWidget(widget)
        self.method_forms.append(widget)

        # DBSCAN cluster
        widget = DBSCANClusteringForm()
        self.method_container_layout.addWidget(widget)
        self.method_forms.append(widget)
        
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addItem(QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        self.previewButton = QtWidgets.QCheckBox("Display clusters")
        h_layout.addWidget(self.previewButton)
        mainLayoutV.addLayout(h_layout)
        
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
        self.previewButton.setChecked(True)
        idx = self.methods.index(method)
        self.method.setCurrentIndex(idx)
        self.method_forms[idx].set_from_config(**params)

    def reset(self):
        self.enableProcessing.setChecked(False)
        self.previewButton.setChecked(False)
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

class ClusteringForm(QtWidgets.QWidget):
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

class AgglomerativeClusteringForm(ClusteringForm):
    def __init__(self, parent=None):
        self.linkage_types = ["single","complete","ward"]
        super().__init__(parent)

    def initView(self):
        # override init view
        h_layout = QtWidgets.QHBoxLayout(self)
        # create dictionary with names labels and widgets
        self.inputs["search_radius"] = {"label":"search radius:","widget": QtWidgets.QDoubleSpinBox()}
        self.inputs["search_radius"]["widget"].setValue(0.5)
        self.inputs["search_radius"]["widget"].setRange(0.0, 2.0)
        self.inputs["search_radius"]["widget"].setSingleStep(0.1)
        self.inputs["linkage"] = {"label":"linkage type:","widget": QtWidgets.QComboBox()}
        [self.inputs["linkage"]["widget"].addItem(i) for i in self.linkage_types]
        self.inputs["is_xy"] = {"label":"only XY:","widget": QtWidgets.QComboBox()}
        [self.inputs["is_xy"]["widget"].addItem(i) for i in ["yes","no"]]
        self.inputs["min_samples"] = {"label":"min samples:","widget": QtWidgets.QSpinBox()}
        self.inputs["min_samples"]["widget"].setRange(5, 500)
        self.inputs["min_samples"]["widget"].setValue(30)
        #self.inputs["leaf_size"] = {"label":"leaf size:","widget": QtWidgets.QSpinBox()}
        #self.inputs["leaf_size"]["widget"].setValue(30)

        f_layout = QtWidgets.QFormLayout()
        h_layout.addLayout(f_layout)
        for k, v in self.inputs.items():
            f_layout.addRow(QtWidgets.QLabel(v["label"]), v["widget"])
        
        spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum)
        h_layout.addItem(spacer)

    def set_from_config(self, search_radius=0.5, linkage="single", is_xy=True, min_samples=30):
        self.inputs["search_radius"]["widget"].setValue(search_radius)
        idx = self.linkage_types.index(linkage)
        self.inputs["linkage"]["widget"].setCurrentIndex(idx)
        idx = 0 if is_xy else 1
        self.inputs["is_xy"]["widget"].setCurrentIndex(idx)
        self.inputs["min_samples"]["widget"].setValue(min_samples)

    def reset(self):
        self.inputs["search_radius"]["widget"].setValue(0.5)
        self.inputs["linkage"]["widget"].setCurrentIndex(0)
        self.inputs["is_xy"]["widget"].setCurrentIndex(0)
        self.inputs["min_samples"]["widget"].setValue(30)
        #self.inputs["leaf_size"]["widget"].setValue(30)

class DBSCANClusteringForm(ClusteringForm):
    def __init__(self, parent=None):
        super().__init__(parent)

    def initView(self):
        # override init view
        h_layout = QtWidgets.QHBoxLayout(self)
        # create dictionary with names labels and widgets
        self.inputs["search_radius"] = {"label":"search radius:","widget": QtWidgets.QDoubleSpinBox()}
        self.inputs["search_radius"]["widget"].setValue(0.5)
        self.inputs["search_radius"]["widget"].setRange(0.0, 2.0)
        self.inputs["search_radius"]["widget"].setSingleStep(0.1)
        self.inputs["is_xy"] = {"label":"only XY:","widget": QtWidgets.QComboBox()}
        [self.inputs["is_xy"]["widget"].addItem(i) for i in ["yes","no"]]
        self.inputs["min_samples"] = {"label":"min samples:","widget": QtWidgets.QSpinBox()}
        self.inputs["min_samples"]["widget"].setRange(5, 500)
        self.inputs["min_samples"]["widget"].setValue(30)
        #self.inputs["leaf_size"] = {"label":"leaf size:","widget": QtWidgets.QSpinBox()}
        #self.inputs["leaf_size"]["widget"].setValue(30)

        f_layout = QtWidgets.QFormLayout()
        h_layout.addLayout(f_layout)
        for k, v in self.inputs.items():
            f_layout.addRow(QtWidgets.QLabel(v["label"]), v["widget"])
        
        spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum)
        h_layout.addItem(spacer)

    def set_from_config(self, search_radius=0.5, is_xy=True, min_samples=30):
        self.inputs["search_radius"]["widget"].setValue(search_radius)
        idx = 0 if is_xy else 1
        self.inputs["is_xy"]["widget"].setCurrentIndex(idx)
        self.inputs["min_samples"]["widget"].setValue(min_samples)

    def reset(self):
        self.inputs["search_radius"]["widget"].setValue(0.5)
        self.inputs["is_xy"]["widget"].setCurrentIndex(0)
        self.inputs["min_samples"]["widget"].setValue(30)
        #self.inputs["leaf_size"]["widget"].setValue(30)


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

    dock = ClusteringDock(parent=win)
    def test_get_config():
        print(dock.getSettings())

    def test_set_config():
        settings = {
            "method": "dbscan",
            "params": {
                "search_radius": 0.5,
                "is_xy": True,
                "min_samples":30
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

