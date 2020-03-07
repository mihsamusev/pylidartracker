from PyQt5 import QtCore, QtGui, QtWidgets
import sys

class ClusteringDock(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # init view and callbacks
        self.initView()
        self._connectOwnButtons()

    def initView(self):
        self.setWindowTitle("Clustering")
        self.setAutoFillBackground(False)
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        # TODO: add options for allowed docking sides, max size, edge outline color

        # set central widget and main layout
        centralWidget = QtWidgets.QWidget()
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
        [self.method.addItem(i) for i in ["naive","dbscan"]]
        layout.addWidget(QtWidgets.QLabel("method:"))
        layout.addWidget(self.method)
        layout.addItem(QtWidgets.QSpacerItem(40, 20,
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        groupLayoutV.addLayout(layout)

        self.method_container_layout = QtWidgets.QStackedLayout()
        groupLayoutV.addLayout(self.method_container_layout)

        # clusters
        self.cluster_forms = []
        # agglomerative cluster
        widget = AgglomerativeClusteringForm()
        self.method_container_layout.addWidget(widget)
        self.cluster_forms.append(widget)

        # DBSCAN cluster
        widget = DBSCANClusteringForm()
        self.method_container_layout.addWidget(widget)
        self.cluster_forms.append(widget)

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

    def _connectOwnButtons(self):
        self.method.currentIndexChanged[int].connect(self.comboOptionChanged)
        self.enableProcessing.clicked.connect(self.toggleProcessing)

    def getSettings(self):
        idx = self.method_container_layout.currentIndex()
        out = {
            "method": self.method.currentText(),
            "params": self.cluster_forms[idx].getState()
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

    def setState(self):
        pass

class AgglomerativeClusteringForm(ClusteringForm):
    def __init__(self, parent=None):
        super().__init__(parent)

    def initView(self):
        # override init view
        h_layout = QtWidgets.QHBoxLayout(self)
        # create dictionary with names labels and widgets
        self.inputs["search_radius"] = {"label":"search radius:","widget": QtWidgets.QDoubleSpinBox()}
        self.inputs["search_radius"]["widget"].setValue(0.1)
        self.inputs["search_radius"]["widget"].setRange(0.0, 2.0)
        self.inputs["search_radius"]["widget"].setSingleStep(0.1)
        self.inputs["linkage"] = {"label":"linkage type:","widget": QtWidgets.QComboBox()}
        [self.inputs["linkage"]["widget"].addItem(i) for i in ["complete","single","ward"]]
        self.inputs["is_xy"] = {"label":"only XY:","widget": QtWidgets.QComboBox()}
        [self.inputs["is_xy"]["widget"].addItem(i) for i in ["no","yes"]]
        self.inputs["min_samples"] = {"label":"min samples:","widget": QtWidgets.QSpinBox()}
        self.inputs["min_samples"]["widget"].setRange(0, 500)

        f_layout = QtWidgets.QFormLayout()
        h_layout.addLayout(f_layout)
        for k, v in self.inputs.items():
            f_layout.addRow(QtWidgets.QLabel(v["label"]), v["widget"])
        
        spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum)
        h_layout.addItem(spacer)

class DBSCANClusteringForm(ClusteringForm):
    def __init__(self, parent=None):
        super().__init__(parent)

    def initView(self):
        # override init view
        h_layout = QtWidgets.QHBoxLayout(self)
        # create dictionary with names labels and widgets
        self.inputs["search_radius"] = {"label":"search radius:","widget": QtWidgets.QDoubleSpinBox()}
        self.inputs["search_radius"]["widget"].setValue(0.1)
        self.inputs["search_radius"]["widget"].setRange(0.0, 2.0)
        self.inputs["search_radius"]["widget"].setSingleStep(0.1)
        self.inputs["is_xy"] = {"label":"only XY:","widget": QtWidgets.QComboBox()}
        [self.inputs["is_xy"]["widget"].addItem(i) for i in ["no","yes"]]
        self.inputs["min_samples"] = {"label":"min samples:","widget": QtWidgets.QSpinBox()}
        self.inputs["min_samples"]["widget"].setRange(0, 500)
        #self.inputs["leaf_size"] = {"label":"leaf size:","widget": QtWidgets.QSpinBox()}
        #self.inputs["leaf_size"]["widget"].setValue(30)

        f_layout = QtWidgets.QFormLayout()
        h_layout.addLayout(f_layout)
        for k, v in self.inputs.items():
            f_layout.addRow(QtWidgets.QLabel(v["label"]), v["widget"])
        
        spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum)
        h_layout.addItem(spacer)

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
    
    dock = ClusteringDock(parent=win)
    win.addDockWidget(QtCore.Qt.DockWidgetArea(2), dock)
    win.show()
    sys.exit(app.exec_())

