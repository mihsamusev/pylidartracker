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
from ui.inputdialog import InputDialog

from controller import Controller
from processing.lidarprocessor import LidarProcessor

class LidarView(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # main window
        self.setWindowTitle("LIBTrAna - Lidar based traffic analysis")
        self.setWindowIcon(QtGui.QIcon("./images/velodyne_hdl.png"))
        self.setMinimumSize(800,600)
        self.centralWidget = QtWidgets.QWidget(parent=self)
        self.centralWidget.setMinimumSize(QtCore.QSize(400, 300))
        self.mainLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.setCentralWidget(self.centralWidget)
        
        self.setDockOptions(QtGui.QMainWindow.AnimatedDocks | QtGui.QMainWindow.AllowTabbedDocks)
        
        self._createMenuBar()
        self._createToolBar()
        self._createToolbarPlayer()
        self._createStatusBar()
        self._createGraphicsDisplay()
        self._createTransformDock()
        self._createClippingDock()
        self._createBackgroundDock()
        self._createClusteringDock()
        self._createTrackingDock()

        self.docks = [
            (self.transformDock, self.actionTransform),
            (self.clippingDock, self.actionClipping),
            (self.backgroundDock, self.actionBackground),
            (self.clusteringDock, self.actionCluster),
            (self.trackingDock, self.actionTracker)]

        # startup blocks of functionality
        self.enableConfigLoading(False)
        self.enableFrameControls(False)
        self.enablePreprocessing(False)
        self.enableClustering(False)
        self.enableTracking(False)
        self.enableOuput(False)

        # variables
        self.player_running = False

        self.connectOwn()

    def connectOwn(self):
        self.actionPlayerRun.triggered.connect(self.switchPlayerState)

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

    def resetAllDocks(self):
        self.transformDock.reset()
        self.clippingDock.reset()
        self.backgroundDock.reset()

    #
    # TOOLBAR RELATED
    #

    def _createToolBar(self):
        # TODO: NO LEFT CLICK ALLOWED AMYBE?
        self.toolBar = QtWidgets.QToolBar(parent=self)
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.toolBar.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.toolBar.setMovable(False)

        # LOAD
        self.actionLoadPCAP = QtWidgets.QAction(parent=self)
        self.actionLoadPCAP.setToolTip('Load .pcap point cloud stream file') 
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/velodyne_hdl.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionLoadPCAP.setIcon(icon)
        self.toolBar.addAction(self.actionLoadPCAP)
        
        # TRANSFORM
        self.toolBar.addSeparator()
        self.actionTransform = QtWidgets.QAction(parent=self)
        self.actionTransform.setToolTip(
            "Define new XY plane for the point clouds")
        self.actionTransform.setCheckable(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/transform.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionTransform.setIcon(icon)
        self.toolBar.addAction(self.actionTransform)

        # CLIP
        self.actionClipping = QtWidgets.QAction(parent=self)
        self.actionClipping.setToolTip(
            "Clip out unnecessary point cloud parts")
        self.actionClipping.setCheckable(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/clipping.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionClipping.setIcon(icon)
        self.toolBar.addAction(self.actionClipping)

        # Background
        self.actionBackground = QtWidgets.QAction(parent=self)
        self.actionBackground.setToolTip(
            "Extract and subtract background part of the point clouds")
        self.actionBackground.setCheckable(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/bg_extraction.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionBackground.setIcon(icon)
        self.toolBar.addAction(self.actionBackground)

        # CLUSTER
        self.toolBar.addSeparator()
        self.actionCluster = QtWidgets.QAction(parent=self)
        self.actionCluster.setToolTip("Calculate point cloud clusters")
        self.actionCluster.setCheckable(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/clustering.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionCluster.setIcon(icon)
        self.toolBar.addAction(self.actionCluster)

        # TRACKER
        self.actionTracker = QtWidgets.QAction(parent=self)
        self.actionTracker.setToolTip("Track point cloud clusters")
        self.actionTracker.setCheckable(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/tracking.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionTracker.setIcon(icon)
        self.toolBar.addAction(self.actionTracker)

        # OUTPUT
        self.toolBar.addSeparator()
        self.actionOutput = QtWidgets.QAction(parent=self)
        self.actionOutput.setToolTip("Generate output file with cluster tracks")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./images/output.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionOutput.setIcon(icon)
        self.toolBar.addAction(self.actionOutput)

    def _createToolbarPlayer(self):
        self.toolBar.addSeparator()
        self.actionPlayerBack = QtWidgets.QAction(
            QtGui.QIcon("./images/player_back.png"),"",self)
        self.toolBar.addAction(self.actionPlayerBack)

        self.actionPlayerRun = QtWidgets.QAction(
            QtGui.QIcon("./images/player_run.png"),"",self)
        self.toolBar.addAction(self.actionPlayerRun)

        self.actionPlayerForward = QtWidgets.QAction(
            QtGui.QIcon("./images/player_forward.png"),"",self)
        self.toolBar.addAction(self.actionPlayerForward)

        self.frameSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.frameSlider.setFixedWidth(200)
        self.toolBar.addWidget(self.frameSlider)
        self.frameSpinBox = QtWidgets.QSpinBox()
        self.toolBar.addWidget(self.frameSpinBox)

    def switchPlayerState(self):
        if self.player_running:
            self.actionPlayerRun.setIcon(
                QtGui.QIcon("./images/player_run.png"))
        else:
            self.actionPlayerRun.setIcon(
                QtGui.QIcon("./images/player_pause.png"))
        self.player_running = not self.player_running

    #
    # DIALOGS
    #
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

    def getProjectRestartMessage(self):
        box = QtWidgets.QMessageBox()
        box.setIcon(QtWidgets.QMessageBox.Information)
        box.setText("Unsaved changes will be lost.\nDo you want to continue?")
        box.setWindowTitle("Open new PCAP")
        box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

        result = box.exec_()
        return result == QtWidgets.QMessageBox.Yes

    def getOutputDialog(self, max_frames):
        dlg = OutputDialog(max_frames, self)
        result = dlg.exec_()
        return (dlg.getSettings(), result == QtWidgets.QDialog.Accepted)

    def getInputDialog(self, max_frames):
        dlg = InputDialog(max_frames, self)
        result = dlg.exec()
        return (dlg.getSettings(), result == QtWidgets.QDialog.Accepted)

    #
    # MENUBAR RELATED
    #
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
        fileMenu.addAction(self.loadConfigMenu)

        self.saveConfigMenu = QtWidgets.QAction('Save config')
        self.saveConfigMenu.setShortcut('Ctrl+S')
        self.saveConfigMenu.setStatusTip('Save JSON project configuration file')
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

    #
    # STATUSBAR RELATED
    #

    def _createStatusBar(self):
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Load .pcap file to start...")
        #self.statusBarMessage = QtWidgets.QLabel("Load .pcap file to start...")
        #self.statusBar.addPermanentWidget(self.statusBarMessage)
        self.statusProgressBar = QtWidgets.QProgressBar()
        self.statusProgressBar.setValue(0)
        self.statusProgressBar.setVisible(False)
        self.statusBar.addPermanentWidget(self.statusProgressBar)

    #
    # DOCKS
    #

    def _createTransformDock(self):
        self.transformDock = TransformDock(parent=self)
        self.transformDock.setVisible(False)
        self.transformDock.setEnabled(False)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.transformDock)

    def showTransformDock(self):
        self.hideAllDocks()
        if not self.transformDock.isVisible():
            self.transformDock.setVisible(True)
            self.transformDock.setEnabled(True)
            self.actionTransform.setChecked(True)

    def _createClippingDock(self):
        self.clippingDock = ClippingDock(parent=self)
        self.clippingDock.setVisible(False)
        self.clippingDock.setEnabled(False)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.clippingDock)

    def showClippingDock(self):
        self.hideAllDocks()
        if not self.clippingDock.isVisible():
            self.clippingDock.setVisible(True)
            self.clippingDock.setEnabled(True)
            self.actionClipping.setChecked(True)

    def _createClusteringDock(self):
        self.clusteringDock = ClusteringDock(parent=self)
        self.clusteringDock.setVisible(False)
        self.clusteringDock.setEnabled(False)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.clusteringDock)

    def showClusteringDock(self):
        self.hideAllDocks()
        if not self.clusteringDock.isVisible():
            self.clusteringDock.setVisible(True)
            self.clusteringDock.setEnabled(True)
            self.actionCluster.setChecked(True)

    def _createBackgroundDock(self):
        self.backgroundDock = BackgroundDock(parent=self)
        self.backgroundDock.setVisible(False)
        self.backgroundDock.setEnabled(False)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.backgroundDock)

    def showBackgroundDock(self):
        self.hideAllDocks()
        if not self.backgroundDock.isVisible():
            self.backgroundDock.setVisible(True)
            self.backgroundDock.setEnabled(True)
            self.actionBackground.setChecked(True)

    def _createTrackingDock(self):
        self.trackingDock = TrackingDock(parent=self)
        self.trackingDock.setVisible(False)
        self.trackingDock.setEnabled(False)
        self.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.trackingDock)

    def showTrackingDock(self):
        self.hideAllDocks()
        if not self.trackingDock.isVisible():
            self.trackingDock.setVisible(True)
            self.trackingDock.setEnabled(True)
            self.actionTracker.setChecked(True)

    def _createGraphicsDisplay(self):
        self.graphicsView = LidarGraphicsView()
        self.mainLayout.addWidget(self.graphicsView)

    def hideAllDocks(self):
        for dock, action in self.docks:
            dock.setVisible(False)
            dock.setEnabled(False)
            action.setChecked(False)

# enables/disables
    def enableAllControls(self, enabled=True):
        self.enableFrameLoading(enabled)
        self.enableFrameControls(enabled)
        self.enableConfigLoading(enabled)
        self.enablePreprocessing(enabled)
        self.enableClustering(enabled)
        self.enableTracking(enabled)
        self.enableOuput(enabled)

    def enableFrameLoading(self, enabled=True):
        self.actionLoadPCAP.setEnabled(enabled)
        self.openFileMenu.setEnabled(enabled)

    def enableConfigLoading(self, enabled=True):
        self.loadConfigMenu.setEnabled(enabled)
        self.saveConfigMenu.setEnabled(enabled)

    def enableFrameControls(self, enabled=True):
        self.actionPlayerBack.setEnabled(enabled)
        self.actionPlayerRun.setEnabled(enabled)
        self.actionPlayerForward.setEnabled(enabled)
        self.frameSlider.setEnabled(enabled)
        self.frameSpinBox.setEnabled(enabled)

    def enablePreprocessing(self, enabled=True):
        self.actionTransform.setEnabled(enabled)
        self.actionClipping.setEnabled(enabled)
        self.actionBackground.setEnabled(enabled)
        self.transformMenu.setEnabled(enabled)
        self.clippingMenu.setEnabled(enabled)
        self.subtractionMenu.setEnabled(enabled)

    def enableClustering(self, enabled=True):
        self.actionCluster.setEnabled(enabled)
        self.clusterMenu.setEnabled(enabled)

    def enableTracking(self, enabled=True):
        self.actionTracker.setEnabled(enabled)
        self.trackerMenu.setEnabled(enabled)

    def enableOuput(self, enabled=True):
        self.actionOutput.setEnabled(enabled)
        self.outputMenu.setEnabled(enabled)

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