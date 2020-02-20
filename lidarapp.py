import sys
import json
import numpy as np
import argparse
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph.opengl as gl
import ui.iconresource_rc

from ui.transformdockui import TransformDock
from ui.clippingdockui import ClippingDock
from ui.lidargraphicsview import LidarGraphicsView

from controller import Controller
from processing.lidarprocessor import LidarProcessor


class LidarView(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # main window
        self.setWindowTitle("Your favorite LIDAR app")
        self.resize(800, 600)
        self.centralWidget = QtWidgets.QWidget(parent=self)
        self.centralWidget.setMinimumSize(QtCore.QSize(400, 300))
        self.mainLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.setCentralWidget(self.centralWidget)

        self._createMenuBar()
        self._createToolBar()
        self._createStatusBar()
        self._createGraphicsDisplay()
        self._createTransformDock()
        self._createClippingDock()
        
    def set_from_config(self, configpath):
        with open(configpath, "r") as read_file:
            config = json.load(read_file)

            #self.graphicsView.init_from_config(config)

            # call docks one by one
            # transform dock
            if "transformer" in config.keys():
                self.transformDock.set_from_config(**config["transformer"]["params"])
            else:
                self.transformDock.reset()
            
            # clipping dock
            if "clipper" in config.keys():
                self.clippingDock.set_from_config(**config["clipper"]["params"])
            else:
                self.clippingDock.reset()
            
    # TOOLBAR RELATED
    def _createToolBar(self):
        self.toolBar = QtWidgets.QToolBar(parent=self)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.toolBar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.toolBar.setMovable(False)

        # LOAD
        self.actionLoadPCAP = QtWidgets.QAction(parent=self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Toolbar/images/velodyne_hdl.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionLoadPCAP.setIcon(icon)
        self.toolBar.addAction(self.actionLoadPCAP)
        
        # TRANSFORM
        self.actionTransform = QtWidgets.QAction(parent=self)
        self.actionTransform.setCheckable(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Toolbar/images/transform.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionTransform.setIcon(icon)
        self.actionTransform.setEnabled(False)
        self.toolBar.addAction(self.actionTransform)

        # CLIP
        self.actionClipping = QtWidgets.QAction(parent=self)
        self.actionClipping.setCheckable(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Toolbar/images/clipping.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionClipping.setIcon(icon)
        self.actionClipping.setEnabled(False)
        self.toolBar.addAction(self.actionClipping)

        # EXTRACT
        self.actionBGExtraction = QtWidgets.QAction(parent=self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Toolbar/images/bg_extraction.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionBGExtraction.setIcon(icon)
        self.actionBGExtraction.setEnabled(False)
        self.toolBar.addAction(self.actionBGExtraction)

        # CLUSTER
        self.actionCluster = QtWidgets.QAction(parent=self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Toolbar/images/clustering.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionCluster.setIcon(icon)
        self.actionCluster.setEnabled(False)
        self.toolBar.addAction(self.actionCluster)

        # TRACK
        self.actionTrack = QtWidgets.QAction(parent=self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Toolbar/images/tracking.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionTrack.setIcon(icon)
        self.actionTrack.setEnabled(False)
        self.toolBar.addAction(self.actionTrack)

        # slider and spin box
        self.toolBar.addSeparator()
        self.frameSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.frameSlider.setFixedWidth(200)
        self.frameSlider.setEnabled(False)
        self.toolBar.addWidget(self.frameSlider)
        self.frameSpinBox = QtWidgets.QSpinBox()
        self.frameSpinBox.setEnabled(False)
        self.toolBar.addWidget(self.frameSpinBox)

    def getPCAPDialog(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open File','',"PCAP Files (*.pcap)")
        return fname[0]

    def getJSONDialog(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open File','',"JSON Files (*.json)")
        return fname[0]

    def setJSONDialog(self):
        fname = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save File','',"JSON Files (*.json)")
        return fname[0]

    # MENUBAR RELATED
    def _createMenuBar(self):
        self.menuBar = QtWidgets.QMenuBar(parent=self)
        self.setMenuBar(self.menuBar)

        fileMenu = self.menuBar.addMenu('&File')

        self.openFileMenu = QtWidgets.QAction('Load PCAP')
        self.openFileMenu.setShortcut('Ctrl+O')
        self.openFileMenu.setStatusTip('Load .pcap point cloud file')
        fileMenu.addAction(self.openFileMenu)

        self.loadConfigMenu = QtWidgets.QAction('Load config')
        self.loadConfigMenu.setShortcut('Ctrl+L')
        self.loadConfigMenu.setStatusTip('Load JSON project configuration file')
        self.loadConfigMenu.setEnabled(False)
        fileMenu.addAction(self.loadConfigMenu)

        self.saveConfigMenu = QtWidgets.QAction('Save config')
        self.saveConfigMenu.setShortcut('Ctrl+S')
        self.saveConfigMenu.setStatusTip('Save JSON project configuration file')
        self.saveConfigMenu.setEnabled(False)
        fileMenu.addAction(self.saveConfigMenu)

    # STATUSBAR RELATED
    def _createStatusBar(self):
        self.statusBar = QtWidgets.QStatusBar(parent=self)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Load .pcap file to start...")

    def _createTransformDock(self):
        self.transformDock = TransformDock(parent=self)
        self.transformDock.setVisible(False)
        self.transformDock.setEnabled(False)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.transformDock)

    def showTransformDock(self):
        if not self.transformDock.isVisible():
            self.transformDock.setVisible(True)
            self.transformDock.setEnabled(True)
        else:
            self.transformDock.setVisible(False)
            self.transformDock.setEnabled(False)

    def _createClippingDock(self):
        self.clippingDock = ClippingDock(parent=self)
        self.clippingDock.setVisible(False)
        self.clippingDock.setEnabled(False)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.clippingDock)

    def showClippingDock(self):
        if not self.clippingDock.isVisible():
            self.clippingDock.setVisible(True)
            self.clippingDock.setEnabled(True)
        else:
            self.clippingDock.setVisible(False)
            self.clippingDock.setEnabled(False)

    # GRAPHICS RELATED -> can be in its own classs
    def _createGraphicsDisplay(self):
        # setup main graphics window
        #self.graphicsView = gl.GLViewWidget()
        self.graphicsView = LidarGraphicsView()
        self.mainLayout.addWidget(self.graphicsView)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    view = LidarView()
    view.show()

    model = LidarProcessor()
    ctrl = Controller(view=view, model=model)

    # for debugging
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--pcap", default=None,
        help="Path to the pcap file")
    ap.add_argument("-f", "--framecount", default=50,
        help="Path to the PCD file containing a background map.")
    ap.add_argument("-c", "--config", default=None,
        help="Path to JSON project config file")
    args = vars(ap.parse_args())

    if args["pcap"] is not None:
        ctrl._loadFrames(args["pcap"], args["framecount"])

    sys.exit(app.exec())