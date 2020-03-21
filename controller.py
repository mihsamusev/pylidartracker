from PyQt5 import QtCore
import numpy as np
from ui.uithread import Worker

class Controller():
    def __init__(self, view, model):
        self._view = view
        self._model = model
        self._connectSignals()
        self._currentFrameIdx = 0
        self._maxFrames = 0
        self.threadpool = QtCore.QThreadPool()
        self.isLatestTransform = False

    def _connectSignals(self):
        # frame scrolling
        self._view.frameSlider.valueChanged.connect(self.frameChanged)
        self._view.frameSpinBox.valueChanged.connect(self.frameChanged)

        # MENUBAR
        self._view.openFileMenu.triggered.connect(self.on_load_pcap)
        self._view.saveConfigMenu.triggered.connect(self.saveProjectConfig)
        self._view.loadConfigMenu.triggered.connect(self.loadProjectConfig)

        # TOOLBAR
        # load 
        self._view.actionLoadPCAP.triggered.connect(self.on_load_pcap)
        
        # transform action
        self._view.actionTransform.triggered.connect(
            self._view.showTransformDock)
        self._view.transformDock.pickBtn.toggled.connect(
            self.allowPointPicking)
        self._view.graphicsView.threePointsPicked.connect(
            self.calculateTransform)
        self._view.transformDock.applyButton.clicked.connect(
            self.applyTransform)

        # clipping action
        self._view.actionClipping.triggered.connect(
            self._view.showClippingDock)
        self._view.clippingDock.valueChanged.connect(
            self.updateCropBox)
        self._view.clippingDock.applyButton.clicked.connect(
            self.applyClipping)

        # background
        self._view.actionBackground.triggered.connect(
            self._view.showBackgroundDock)
        self._view.backgroundDock.extractButton.clicked.connect(
            self.extractBackground)
        self._view.backgroundDock.loadButton.clicked.connect(self.loadBackground)
        self._view.backgroundDock.saveButton.clicked.connect(self.saveBackground)
        # quckie
        self._view.backgroundDock.previewButton.stateChanged.connect(
            self.previewBackground)
        self._view.backgroundDock.applyButton.clicked.connect(
            self.applySubtraction)

        # clusteirng
        self._view.actionCluster.triggered.connect(self._view.showClusteringDock)
        self._view.clusteringDock.applyButton.clicked.connect(self.applyClustering)
        self._view.clusteringDock.previewButton.stateChanged.connect(
            self.previewClusters)

        # tracking
        self._view.actionTracker.triggered.connect(self._view.showTrackingDock)
        self._view.trackingDock.applyButton.clicked.connect(self.applyTracking)
    #
    # I/O
    #
    def loadProjectConfig(self):
        configpath = self._view.getJSONDialog()
        if not configpath:
            return

        self._model.init_from_config(configpath)

        # runs on a thread that reports progress
        # and updates the inteface on completion
        self.apply_preprocessing()
        
        self._view.set_from_config(configpath)

    def saveProjectConfig(self):
        configpath = self._view.setJSONDialog()
        if not configpath:
            return
        self._model.save_config(configpath)

    def loadFrames(self):
        fname = self._view.getPCAPDialog()
        if not fname:
            return

        self._model.setFilename(fname)

        # TODO: can ask which callib file to support more lidars
        self._model.restartBuffering()

        # read some frames
        self._maxFrames = 100 
        self._model.loadNFrames(100)

        # update scroller
        self.updateDataScrollers()
        # for flexin visuals
        self.updateGraphicsView()
        
        # unblock other actions
        self.allowToolbarActions(True)
        self.allowMenuActions(True)

    def _loadFrames(self, filename, count):
        self._model.setFilename(filename)

        # TODO: can ask which callib file to support more lidars
        self._model.restartBuffering()

        # read some frames
        self._maxFrames = count
        self._model.loadNFrames(self._maxFrames)

        # update scroller
        self.updateDataScrollers()
        # for flexin visuals
        self.updateGraphicsView()
        
        # unblock other actions
        self.allowToolbarActions(True)
        self.allowMenuActions(True)

    def on_load_pcap(self):
        fname = self._view.getPCAPDialog()
        if not fname:
            return

        # read some frames
        count=100
        self._maxFrames = count #TODO: dialog for that

        # activate status bar
        self._view.statusBar.showMessage("Reading point cloud data ...")
        self._view.statusProgressBar.setVisible(True)

        # Pass the function to execute
        worker = Worker(self.load_frames, fname, self._maxFrames)
        worker.signals.progress.connect(self.frame_processing_progress)
        worker.signals.finished.connect(self.frame_loading_complete)
        
        # Execute worker
        self.threadpool.start(worker)

    def frame_processing_progress(self, n):
        self._view.statusProgressBar.setValue(n)

    def frame_loading_complete(self):
        self._view.statusBar.showMessage("Point clouds loaded")
        self._view.statusProgressBar.setValue(0)
        self._view.statusProgressBar.setVisible(False)

        # update scroller
        self.updateDataScrollers()
        # for flexin visuals
        self.updateGraphicsView()

        self.allowToolbarActions(True)
        self.allowMenuActions(True)

    def load_frames(self, filename, count, progress_callback):
        self._model.setFilename(filename)
        self._model.restartBuffering()
        self._model.resetProcessor()
        for n in range(count):
            self._model.loadFrame()
            progress_callback.emit((n+1)*100/(count))

    #
    # MODEL UPDATING
    #
    def _apply_preprocessing_fn(self, progress_callback):
        for p in self._model.updatePreprocessedGen():
            progress_callback.emit(p)

    def apply_preprocessing(self):
        # activate status bar
        self._view.statusBar.showMessage("Applying preprocessing ...")
        self._view.statusProgressBar.setVisible(True)

        # TODO: block buttons

        # Pass the function to execute worker task
        worker = Worker(self._apply_preprocessing_fn)
        worker.signals.progress.connect(self.frame_processing_progress)
        worker.signals.finished.connect(self.frame_preprocessing_complete)
        self.threadpool.start(worker)

    def frame_preprocessing_complete(self):
        self._view.statusBar.showMessage("Point clouds preprocessed")
        self._view.statusProgressBar.setValue(0)
        self._view.statusProgressBar.setVisible(False)

        self.updateGraphicsView()

        #self.allowToolbarActions(True)
        #self.allowMenuActions(True)


    #
    # PLANE FITTING AND TRANSFORM ACTON
    #
    def allowPointPicking(self):
        if self._view.transformDock.pickBtn.isChecked():
            # update dock
            self._view.transformDock.pickBtn.setText("Stop point picking")
            self._view.graphicsView.setSelectedVisible(True)
            self._view.transformDock.enableResults(False)
            self._view.transformDock.updateResult(None)
            
            # update graphics view settings
            self._view.graphicsView.setSelectionAllowed(True)
            self._view.graphicsView.resetSelected()

            # update model
            self._model.destroyTransformer()

        else:
            self._view.transformDock.pickBtn.setText("Start point picking")
            self._view.graphicsView.setSelectionAllowed(False)
            
            if self._view.graphicsView.nSelected != 3:
                self._view.graphicsView.resetSelected()
                self._view.transformDock.updateResult(None)
                # update model
                self._model.destroyTransformer()
            else:
                self._view.transformDock.enableResults(True)

    def calculateTransform(self):
        pts = self._view.graphicsView.getSelectedPoints()
        self._model.createTransformer(points=pts)

        # draw reults on widget and plane on the screen
        normal, intercept = self._model.getPlaneCoeff()
        self._view.transformDock.updateResult(normal, intercept)
        
        self._view.transformDock.pickBtn.setChecked(False)

    def applyTransform(self):
        if self._view.transformDock.enableTransform.isChecked():
            self._view.graphicsView.setSelectedVisible(False)
            self.apply_preprocessing()
        else:
            self._view.transformDock.updateResult(None)
            self._model.destroyTransformer()
            self.apply_preprocessing()

        # update view and status bar
        self.updateGraphicsView()

    #
    # CLIPPING ACTION
    #
    def applyClipping(self):
        settings = self._view.clippingDock.getSettings()
        
        # define clipper at model
        self._model.createClipper(method="polygon", **settings["params"])

        if settings["transform"]:
            self.apply_preprocessing()
        else:
            self._view.clippingDock.reset()
            self._model.destroyClipper()
            self.apply_preprocessing()

        #update view and status bar
        self.updateGraphicsView()

    #
    # BG EXTRACTION / SUBTRACTION
    #
    def extractBackground(self):
        settings = self._view.backgroundDock.getSettings()
        self._model.extractBackground(method=settings["extractor"]["method"],
            **settings["extractor"]["params"])

        self._view.backgroundDock.savedLabel.setText("Background not saved")
        self._view.backgroundDock.extractedLabel.setText("Background extracted")
        self._view.backgroundDock.previewButton.setEnabled(True)

    def loadBackground(self):
        bgpath = self._view.backgroundDock.getCSVDialog()
        if not bgpath:
            return
        self._model.loadBackground(bgpath)
        self._view.backgroundDock.loadedLabel.setText("Background loaded")
        self._view.backgroundDock.previewButton.setEnabled(True)

    def saveBackground(self):
        bgpath = self._view.backgroundDock.setCSVDialog()
        if not bgpath:
            return
        self._model.saveBackground(bgpath)
        self._view.backgroundDock.savedLabel.setText("Background saved")

    def applySubtraction(self):
        settings = self._view.backgroundDock.getSettings()
        if self._view.backgroundDock.enableSubtraction.isChecked():
            self._model.createBgSubtractor(method=settings["subtractor"]["method"],
            **settings["subtractor"]["params"])
            self.apply_preprocessing()
        else:
            self._model.destroyBgSubtractor()
            self.apply_preprocessing()

        #update view and status bar
        self.updateGraphicsView()
    #
    # CLUSTERING
    #
    def applyClustering(self):
        if self._view.clusteringDock.enableProcessing.isChecked():
            settings = self._view.clusteringDock.getSettings()
            settings["params"]["is_xy"] = True if settings["params"]["is_xy"].lower() == "yes" else False
            
            print("[DEBUG]\n{}".format(settings))
            self._model.extractClusters(method=settings["method"], **settings["params"])
        else:
            self._model.destroyClusterer()
        self.previewClusters()

    #
    # TRACKING
    #
    
    def applyTracking(self):
        if self._view.trackingDock.enableProcessing.isChecked():
            settings = self._view.trackingDock.getSettings()
            self._model.trackClusters(method=settings["method"], **settings["params"])
        else:
            print("not doing crap")
            self._model.destroyTracker()
        self.previewClusters()
    
    #
    # UI UPDATES
    #
    def frameChanged(self, idx):
        self._view.frameSpinBox.setValue(idx)
        self._view.frameSlider.setValue(idx)
        self._currentFrameIdx = idx
        self.updateGraphicsView()

    def allowToolbarActions(self, enabled=True):
        self._view.actionTransform.setEnabled(enabled)
        self._view.actionClipping.setEnabled(enabled)
        self._view.actionBackground.setEnabled(enabled)
        self._view.actionCluster.setEnabled(enabled)
        self._view.actionTracker.setEnabled(enabled)
        self._view.frameSlider.setEnabled(enabled)
        self._view.frameSpinBox.setEnabled(enabled)

    def allowMenuActions(self, enabled=True):
        self._view.loadConfigMenu.setEnabled(enabled)
        self._view.saveConfigMenu.setEnabled(enabled)

    def updateDataScrollers(self):
        self._view.frameSlider.setMaximum(self._maxFrames-1)
        self._view.frameSlider.setValue(self._currentFrameIdx)
        self._view.frameSpinBox.setMaximum(self._maxFrames-1)
        self._view.frameSpinBox.setValue(self._currentFrameIdx)

    #
    # GRAPHICS UPDATE
    #
    def previewBackground(self):
        self.updateBackgroundPoints()
        self._view.graphicsView.draw()

    def previewClusters(self):
            self.updateClusters()
            self._view.graphicsView.draw()

    def updateClusters(self):
        boxes = []
        labels = []
        if self._view.clusteringDock.previewButton.isChecked():
            clusters = self._model.getClusters(self._currentFrameIdx)
            for c in clusters:
                boxes.append(c.getOOBB())
                labels.append(c.id)
        self._view.graphicsView.setClusterAABB(boxes)
        self._view.graphicsView.setClusterLabels(labels)

    def updateBackgroundPoints(self):
        if self._view.backgroundDock.previewButton.isChecked():
            self._view.graphicsView.setBackgroundPoints(self._model.preprocessedBgArray)
        else:
            self._view.graphicsView.setBackgroundPoints(None)

    def updateRawPoints(self):
        pts = self._model.getArray(self._currentFrameIdx)
        if pts is None:
            return
        self._view.graphicsView.setRawPoints(pts)

    def updateCropBox(self):
        settings = self._view.clippingDock.getSettings()

        if settings["display"]:
            self._view.graphicsView.setCropBox(polygon=settings["params"]["polygon"],
                zrange=settings["params"]["z_range"])
        else:
            self._view.graphicsView.setCropBox(polygon=None, zrange=None)
        self._view.graphicsView.draw()

    def updateGraphicsView(self):
        self.updateRawPoints()
        self.updateBackgroundPoints()
        self.updateClusters()
        self._view.graphicsView.draw()
