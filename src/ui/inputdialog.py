from PyQt5 import QtCore, QtGui, QtWidgets
import sys

class InputDialog(QtWidgets.QDialog):
    def __init__(self, max_frames, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags()
                    ^ QtCore.Qt.WindowContextHelpButtonHint)
        # init view and callbacks
        self.max_frames = max_frames
        
        self.setModal(True)
        self.initView()
        self.setFixedWidth(200)
        self.setFixedHeight(150)

        self._connectOwnButtons()

    def initView(self):
        self.setWindowTitle("Load PCAP")
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
        self.to_frame.setRange(1, self.max_frames)
        self.to_frame.setValue(100)
        f_layout.addRow(QtWidgets.QLabel("to frame"), self.to_frame)
        f_layout.addRow(
            QtWidgets.QLabel("total frames"),
            QtWidgets.QLabel(str(self.max_frames)))

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
        self.dialogButtons.accepted.connect(self.accept)
        self.dialogButtons.rejected.connect(self.reject)
        self.to_frame.valueChanged.connect(self.update_offset)

    def update_offset(self):
        self.from_frame.setRange(0, self.to_frame.value() - 1)

    def getSettings(self):
        out = {
            "from_frame": self.from_frame.value(),
            "to_frame": self.to_frame.value()
        }
        return out

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = InputDialog(666)
    dialog.show()
    sys.exit(app.exec_())