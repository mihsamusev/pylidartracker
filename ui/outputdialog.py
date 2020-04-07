from PyQt5 import QtCore, QtGui, QtWidgets
import sys

class OutputDialog(QtWidgets.QDialog):
    def __init__(self, max_frames, parent=None):
        super().__init__(parent)
        self.setModal(True)
        # init view and callbacks
        self.max_frames = max_frames
        self.initView()
        self._connectOwnButtons()

    def initView(self):
        self.setWindowTitle("Ouptut writter options")
        #self.resize(400, 300)
        mainLayoutV = QtWidgets.QVBoxLayout(self)

        h_layout = QtWidgets.QHBoxLayout()
        mainLayoutV.addLayout(h_layout)
        f_layout = QtWidgets.QFormLayout()
        h_layout.addLayout(f_layout)

        self.from_frame = QtWidgets.QSpinBox()
        self.from_frame.setValue(0)
        self.from_frame.setRange(0, self.max_frames)
        f_layout.addRow(QtWidgets.QLabel("from frame"), self.from_frame)
        
        self.to_frame = QtWidgets.QSpinBox()
        self.to_frame.setRange(0, self.max_frames)
        self.to_frame.setValue(self.max_frames)
        f_layout.addRow(QtWidgets.QLabel("to frame"), self.to_frame)
        f_layout.addRow(
            QtWidgets.QLabel("total frames"),
            QtWidgets.QLabel(str(self.max_frames)))

        self.method = QtWidgets.QComboBox()
        [self.method.addItem(i) for i in ["tracked_clusters"]] #,"edited_point_clouds"]
        f_layout.addRow(QtWidgets.QLabel("output type"), self.method)

        spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum)
        h_layout.addItem(spacer)

        self.method_container_layout = QtWidgets.QStackedLayout()
        mainLayoutV.addLayout(self.method_container_layout)

        # different types od ourpur
        self.method_forms = []
        # Tracked Clusters
        widget = TrackedClustersForm()
        self.method_container_layout.addWidget(widget)
        self.method_forms.append(widget)

        # Edited clouds
        widget = EditedCloudForm()
        self.method_container_layout.addWidget(widget)
        self.method_forms.append(widget)

        # apply button
        applyLayoutH = QtWidgets.QHBoxLayout()
        applyLayoutH.addItem(QtWidgets.QSpacerItem(40, 20,
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        self.dialogButtons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        applyLayoutH.addWidget(self.dialogButtons)
        mainLayoutV.addLayout(applyLayoutH)

        '''# status and progress
        self.status = QtWidgets.QLabel("here gonna do status ting")
        mainLayoutV.addWidget(self.status)

        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setValue(1)
        mainLayoutV.addWidget(self.progressBar)'''

    def _connectOwnButtons(self):
        self.method.currentIndexChanged[int].connect(self.comboOptionChanged)
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)
    
    def getSettings(self):
        idx = self.method_container_layout.currentIndex()
        out = {
            "output_type": self.method.currentText(),
            "from_frame": self.from_frame.value(),
            "to_frame": self.to_frame.value(),
            "params": self.method_forms[idx].getState()
        }
        return out

    def comboOptionChanged(self, idx):
        self.method_container_layout.setCurrentIndex(idx)

class OutputTypeForm(QtWidgets.QWidget):
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

class EditedCloudForm(OutputTypeForm):
    def __init__(self, parent=None):
        super().__init__(parent)

    def initView(self):
        # override init view
        h_layout = QtWidgets.QHBoxLayout(self)
        # create dictionary with names labels and widgets
        self.inputs["file_format"] = {"label":"file format:","widget": QtWidgets.QComboBox()}
        [self.inputs["file_format"]["widget"].addItem(i) for i in ["pcap","hdf5"]]

        f_layout = QtWidgets.QFormLayout()
        h_layout.addLayout(f_layout)
        for k, v in self.inputs.items():
            f_layout.addRow(QtWidgets.QLabel(v["label"]), v["widget"])
        
        spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum)
        h_layout.addItem(spacer)

class TrackedClustersForm(OutputTypeForm):
    def __init__(self, parent=None):
        super().__init__(parent)

    def initView(self):
        # override init view
        h_layout = QtWidgets.QHBoxLayout(self)
        # create dictionary with names labels and widgets
        self.inputs["file_format"] = {"label":"file format:","widget": QtWidgets.QComboBox()}
        [self.inputs["file_format"]["widget"].addItem(i) for i in ["json","csv"]]
        #self.inputs["include_boxes"] = {"label":"include cluster boxes:","widget": QtWidgets.QComboBox()}
        #[self.inputs["include_boxes"]["widget"].addItem(i) for i in ["yes","no"]]

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
    dialog = OutputDialog(666)
    dialog.show()
    sys.exit(app.exec_())