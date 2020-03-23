import sys
import json
import numpy as np
import argparse
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph.opengl as gl

from ui.transformdockui import TransformDock
from ui.clippingdockui import ClippingDock
from ui.lidargraphicsview import LidarGraphicsView
from ui.backgrounddock import BackgroundDock
from ui.clusteringdock import ClusteringDock
from ui.trackingdock import TrackingDock
from ui.outputdialog import OutputDialog

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
        self._createBackgroundDock()
        self._createClusteringDock()
        self._createTrackingDock()

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

            if "background" in config.keys():
                # TODO: check that it contains "path, extractor, subtractor",
                # otherwise reject and throw warning that bg information
                self.backgroundDock.set_from_config(**config["background"])
            else:
                self.backgroundDock.reset()

    # TOOLBAR RELATED
    def _createToolBar(self):
        # TODO: NO LEFT CLICK ALLOWED AMYBE?
        self.toolBar = QtWidgets.QToolBar(parent=self)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.toolBar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.toolBar.setMovable(False)

        # LOAD
        self.actionLoadPCAP = QtWidgets.QAction(parent=self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/velodyne_hdl.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionLoadPCAP.setIcon(icon)
        self.toolBar.addAction(self.actionLoadPCAP)
        
        # TRANSFORM
        self.toolBar.addSeparator()
        self.actionTransform = QtWidgets.QAction(parent=self)
        self.actionTransform.setCheckable(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/transform.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionTransform.setIcon(icon)
        self.actionTransform.setEnabled(False)
        self.toolBar.addAction(self.actionTransform)

        # CLIP
        self.actionClipping = QtWidgets.QAction(parent=self)
        self.actionClipping.setCheckable(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/clipping.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionClipping.setIcon(icon)
        self.actionClipping.setEnabled(False)
        self.toolBar.addAction(self.actionClipping)

        # Background
        self.actionBackground = QtWidgets.QAction(parent=self)
        self.actionBackground.setCheckable(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/bg_extraction.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionBackground.setIcon(icon)
        self.actionBackground.setEnabled(False)
        self.toolBar.addAction(self.actionBackground)

        # CLUSTER
        self.toolBar.addSeparator()
        self.actionCluster = QtWidgets.QAction(parent=self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/clustering.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionCluster.setIcon(icon)
        self.actionCluster.setEnabled(False)
        self.toolBar.addAction(self.actionCluster)

        # TRACKER
        self.actionTracker = QtWidgets.QAction(parent=self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/tracking.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionTracker.setIcon(icon)
        self.actionTracker.setEnabled(False)
        self.toolBar.addAction(self.actionTracker)

        # OUTPUT
        self.toolBar.addSeparator()
        self.actionOutput = QtWidgets.QAction(parent=self)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/output.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionOutput.setIcon(icon)
        self.actionOutput.setEnabled(False)
        self.toolBar.addAction(self.actionOutput)

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

        fileMenu = self.menuBar.addMenu('File')

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

        editMenu = self.menuBar.addMenu('Edit')
        self.transformMenu = QtWidgets.QAction('Rotate data')
        editMenu.addAction(self.transformMenu)
        self.clippingMenu = QtWidgets.QAction('Clip data')
        editMenu.addAction(self.clippingMenu)
        self.subtractionMenu = QtWidgets.QAction('Subtract background')
        editMenu.addAction(self.subtractionMenu)

        analyzeMenu = self.menuBar.addMenu('Analyze')
        self.clusterMenu = QtWidgets.QAction('Cluster data')
        analyzeMenu.addAction(self.clusterMenu)
        self.trackerMenu = QtWidgets.QAction('Track clusters')
        analyzeMenu.addAction(self.trackerMenu)

        runMenu = self.menuBar.addMenu('Run')
        self.outputMenu = QtWidgets.QAction('Generate output')
        runMenu.addAction(self.outputMenu)

    # STATUSBAR RELATED
    def _createStatusBar(self):
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Load .pcap file to start...")

        self.statusProgressBar = QtWidgets.QProgressBar()
        self.statusProgressBar.setValue(0)
        self.statusProgressBar.setVisible(False)
        self.statusBar.addPermanentWidget(self.statusProgressBar)

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

    def _createClusteringDock(self):
        self.clusteringDock = ClusteringDock(parent=self)
        self.clusteringDock.setVisible(False)
        self.clusteringDock.setEnabled(False)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.clusteringDock)

    def showClusteringDock(self):
        if not self.clusteringDock.isVisible():
            self.clusteringDock.setVisible(True)
            self.clusteringDock.setEnabled(True)
        else:
            self.clusteringDock.setVisible(False)
            self.clusteringDock.setEnabled(False)

    def _createBackgroundDock(self):
        self.backgroundDock = BackgroundDock(parent=self)
        self.backgroundDock.setVisible(False)
        self.backgroundDock.setEnabled(False)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.backgroundDock)

    def showBackgroundDock(self):
        if not self.backgroundDock.isVisible():
            self.backgroundDock.setVisible(True)
            self.backgroundDock.setEnabled(True)
        else:
            self.backgroundDock.setVisible(False)
            self.backgroundDock.setEnabled(False)

    def _createTrackingDock(self):
        self.trackingDock = TrackingDock(parent=self)
        self.trackingDock.setVisible(False)
        self.trackingDock.setEnabled(False)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.trackingDock)

    def showTrackingDock(self):
        if not self.trackingDock.isVisible():
            self.trackingDock.setVisible(True)
            self.trackingDock.setEnabled(True)
        else:
            self.trackingDock.setVisible(False)
            self.trackingDock.setEnabled(False)

    def _createGraphicsDisplay(self):
        self.graphicsView = LidarGraphicsView()
        self.mainLayout.addWidget(self.graphicsView)

    def getOutputDialog(self, max_frames):
        outputDialog = OutputDialog(max_frames, self)
        result = outputDialog.exec_()
        return (outputDialog.getSettings(), result == QtWidgets.QDialog.Accepted)


if __name__ == "__main__":
    # for debugging
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--pcap", default=None,
        help="Path to the pcap file")
    ap.add_argument("-f", "--framecount", default=50, type=int,
        help="Path to the PCD file containing a background map.")
    ap.add_argument("-c", "--config", default=None,
        help="Path to JSON project config file")
    args = vars(ap.parse_args())

    app = QtWidgets.QApplication(sys.argv)
    view = LidarView()
    view.show()

    model = LidarProcessor()
    ctrl = Controller(view=view, model=model)

    # for faster debug
    #if args["pcap"] is not None:
        #ctrl.on_load_pcap(filename=args["pcap"], count=args["framecount"])

    #if args["config"] is not None:
        #ctrl.loadProjectConfig(configpath=args["config"])

    sys.exit(app.exec())