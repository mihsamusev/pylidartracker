import sys
from PyQt5 import QtCore, QtGui, QtWidgets

class DoubleSpinBoxDelegate(QtWidgets.QItemDelegate):
    def __init__(self, decimals=2, parent=None):
        QtWidgets.QItemDelegate.__init__(self, parent=parent)
        self.decimals = decimals

    def createEditor(self, parent, option, index):
        # set settings for spin box
        self.sb = QtWidgets.QDoubleSpinBox(parent)
        self.sb.setDecimals(self.decimals)
        self.sb.setSingleStep(1)
        self.sb.setRange(-200.0, 200.0)
        self.sb.setValue(0.0)
        return self.sb

class XYTable(QtWidgets.QTableWidget):
    valueChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = [[0.0, 0.0]]

        self.decimals = 2
        self.delegate = DoubleSpinBoxDelegate(self.decimals)
        self.setItemDelegate(self.delegate)

        self.setRowCount(1)
        self.setColumnCount(2)
        self.setItem(0, 0, QtWidgets.QTableWidgetItem(
            "{0:.{1}f}".format(0.0, self.decimals)))
        self.setItem(0, 1, QtWidgets.QTableWidgetItem(
            "{0:.{1}f}".format(0.0, self.decimals)))

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setFixedWidth(120)
        self.setHorizontalHeaderLabels(("X","Y"))
        header = self.horizontalHeader()
        header.setFrameStyle(QtWidgets.QFrame.HLine)
        header.setLineWidth(1)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.itemChanged.connect(self._updatedata)


    def setData(self, data):
        if data is None:
            self.setRowCount(1)
            self.setStandardRow(0)
        else:
            self.setRowCount(len(data))
            for i in range(self.rowCount()):
                self.setStandardRow(i, data[i])
    
    def setStandardRow(self, row, xy=[0.0, 0.0]):
        self.setItem(row, 0, QtWidgets.QTableWidgetItem(
            "{0:.{1}f}".format(xy[0], self.decimals)))
        self.setItem(row, 1, QtWidgets.QTableWidgetItem(
            "{0:.{1}f}".format(xy[1], self.decimals)))

    def _addabove(self):
        selected = self.selectedIndexes()
        row = selected[0].row() if selected else 0
        self.insertRow(row)
        self.setStandardRow(row)

    def _addbelow(self):
        selected = self.selectedIndexes()
        row = (selected[0].row() + 1) if selected else self.rowCount()
        self.insertRow(row)
        self.setStandardRow(row)

    def _removerow(self):
        selected = self.selectedIndexes()
        if selected:
            rows = list(set([s.row() for s in selected]))
            changeCount = 0
            for r in rows:
                r -= changeCount
                self.removeRow(r)
                changeCount +=1
            # update data
            self._updatedata()

    def _updatedata(self):
        self._data = []
        for i in range(self.rowCount()):
            row = []
            for j in range(self.columnCount()):
                if self.item(i, j) is None:
                    return
                value = self.item(i, j).text()
                row.append(float(value))
            self._data.append(row)
        self.valueChanged.emit()

    def _add_x(self, value):
        for i in range(self.rowCount()):
            self._data[i][0] += value
            self.setItem(i, 0, QtWidgets.QTableWidgetItem(
            "{0:.{1}f}".format(self._data[i][0], self.decimals)))

    def _add_y(self, value):
        for i in range(self.rowCount()):
            self._data[i][1] += value
            self.setItem(i, 1, QtWidgets.QTableWidgetItem(
            "{0:.{1}f}".format(self._data[i][1], self.decimals)))

    def getData(self):
        return self._data

class ThirdTabLoads(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ThirdTabLoads, self).__init__(parent)    

        self.table = XYTable()

        addabove_button = QtWidgets.QPushButton("Add above")
        addabove_button.clicked.connect(self.table._addabove)

        addbelow_button = QtWidgets.QPushButton("Add below")
        addbelow_button.clicked.connect(self.table._addbelow)

        delete_button = QtWidgets.QPushButton("Delete")
        delete_button.clicked.connect(self.table._removerow)

        get_button = QtWidgets.QPushButton("Get Data")
        get_button.clicked.connect(self.printData)

        addx_button = QtWidgets.QPushButton("X + 1")
        addx_button.clicked.connect(self.addX)
        self.addx_dsb = QtWidgets.QDoubleSpinBox()
        self.addx_dsb.setRange(-20,20)
        self.addx_dsb.setValue(1.0)
        addx_layout = QtWidgets.QHBoxLayout()
        addx_layout.addWidget(addx_button)
        addx_layout.addWidget(self.addx_dsb)

        addy_button = QtWidgets.QPushButton("Y + 2")
        addy_button.clicked.connect(self.addY)
        self.addy_dsb = QtWidgets.QDoubleSpinBox()
        self.addy_dsb.setRange(-20,20)
        self.addy_dsb.setValue(-3.2)
        addy_layout = QtWidgets.QHBoxLayout()
        addy_layout.addWidget(addy_button)
        addy_layout.addWidget(self.addy_dsb)

        set_button = QtWidgets.QPushButton("Set my data")
        set_button.clicked.connect(self.setSomeData)

        buttonSpacerV = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Expanding)

        button_layout = QtWidgets.QVBoxLayout()
        button_layout.addWidget(addabove_button)
        button_layout.addWidget(addbelow_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(get_button)
        button_layout.addLayout(addx_layout)
        button_layout.addLayout(addy_layout)
        button_layout.addWidget(set_button)
        button_layout.addItem(buttonSpacerV)

        tablehbox = QtWidgets.QHBoxLayout()
        tablehbox.setContentsMargins(10, 10, 10, 10)
        tablehbox.addWidget(self.table)

        grid = QtWidgets.QGridLayout(self)
        grid.addLayout(button_layout, 0, 1)
        grid.addLayout(tablehbox, 0, 0)

    def printData(self):
        data = self.table.getData()
        print(data)

    def addX(self):
        value = self.addx_dsb.value()
        self.table._add_x(value)

    def addY(self):
        value = self.addy_dsb.value()
        self.table._add_y(value)

    def setSomeData(self):
        data = [[-13, 5.33],[8.4, 0.0],[-10, 33]]
        data = None
        self.table.setData(data)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = ThirdTabLoads()
    w.show()
    sys.exit(app.exec_())