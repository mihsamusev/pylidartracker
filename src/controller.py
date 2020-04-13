from PyQt5 import QtCore
from PyQt5 import QtWidgets
import numpy as np
from ui.uithread import Worker
import json
from processing.outputwritter import OutputWriter
import os

class Controller():
    def __init__(self, view, model):
        self._view = view
        self._model = model
        self._connectSignals()
        self._currentFrameIdx = 0
        self._scrool_time = 100

        self.pcap_filename = None
        self.config_filename = None
        self._loaded_frame_count = 0
        self._pcap_frame_count = 0

        self.threadpool = QtCore.QThreadPool()
        self.items_status = {
            "transform": False,
            "clipping": False,
            "background_extraction": False,
            "background_subtraction": False,
            "clustering": False,
            "tracking": False
        }

    def _connectSignals(self):
        # frame scrolling
        self._view.frameSlider.valueChanged.connect(self.frameChanged)
        self._view.frameSpinBox.valueChanged.connect(self.frameChanged)
        self._view.actionPlayerRun.triggered.connect(self.playFrameSequence)
        self._view.actionPlayerForward.triggered.connect(self.moveFrameSequenceForward)
        self._view.actionPlayerBack.triggered.connect(self.moveFrameSequenceBackward)

        # MENUBAR
        self._view.openFileMenu.triggered.connect(self.analyze_pcap)
        self._view.saveConfigMenu.triggered.connect(self.saveProjectConfig)
        self._view.loadConfigMenu.triggered.connect(self.load_config)

        # TOOLBAR
        # load 
        self._view.actionLoadPCAP.triggered.connect(self.analyze_pcap)
        
        # transform dock
        self._view.actionTransform.triggered.connect(
            self._view.showTransformDock)
        self._view.transformDock.pickBtn.toggled.connect(
            self.allowPointPicking)
        self._view.graphicsView.threePointsPicked.connect(
            self.calculateTransform)
        self._view.transformDock.applyButton.clicked.connect(
            self.applyTransform)

        # clipping dock
        self._view.actionClipping.triggered.connect(
            self._view.showClippingDock)
        self._view.clippingDock.valueChanged.connect(
            self.updateCropBox)
        self._view.clippingDock.applyButton.clicked.connect(
            self.applyClipping)

        # background dock
        self._view.actionBackground.triggered.connect(
            self._view.showBackgroundDock)
        self._view.backgroundDock.extractButton.clicked.connect(
            self.extractBackground)
        self._view.backgroundDock.loadButton.clicked.connect(self.loadBackground)
        self._view.backgroundDock.saveButton.clicked.connect(self.saveBackground)

        self._view.backgroundDock.previewButton.stateChanged.connect(
            self.previewBackground)
        self._view.backgroundDock.applyButton.clicked.connect(
            self.applySubtraction)

        # clusteirng dock
        self._view.actionCluster.triggered.connect(self._view.showClusteringDock)
        self._view.clusteringDock.applyButton.clicked.connect(self.applyClustering)
        self._view.clusteringDock.previewButton.stateChanged.connect(
            self.previewClusters)

        # tracking dock
        self._view.actionTracker.triggered.connect(self._view.showTrackingDock)
        self._view.trackingDock.applyButton.clicked.connect(self.applyTracking)

        # output dialog
        self._view.actionOutput.triggered.connect(self.generate_output)
        self._view.outputMenu.triggered.connect(self.generate_output)
    #
    # I/O
    #
    # config
    def loadProjectConfig(self):
        # stop player
        self.finish_playing()

        configpath = self._view.getJSONDialog()
        if not configpath:
            return

        self._model.init_from_config(configpath)

        # runs on a thread that reports progress
        # and updates the inteface on completion
        self.apply_preprocessing()
        
        self._view.set_from_config(configpath)

    def load_config(self):
        # stop player
        self.finish_playing()

        configpath = self._view.getJSONDialog()
        if not configpath:
            return
        self.config_filename = configpath

        self._model.init_from_config(self.config_filename)

        # lock buttons, activate status bar
        self._view.enableAllControls(False)
        self._view.statusBar.showMessage("Applying project configuration...")
        self._view.statusProgressBar.setVisible(True)

        # Pass the function to execute
        worker = Worker(self.load_config_fn)
        worker.signals.progress.connect(self.load_config_progress)
        worker.signals.finished.connect(self.load_config_completed)
        self.threadpool.start(worker)

    def load_config_fn(self, progress_callback):
        for p in self._model.updateProcessingGen():
            progress_callback.emit(p)

    def load_config_progress(self, n):
        self._view.statusProgressBar.setValue(n)

    def load_config_completed(self):
        self._view.statusProgressBar.setValue(0)
        self._view.statusProgressBar.setVisible(False)

        self._view.set_from_config(self.config_filename)

        self._view.statusBar.showMessage("")

        # enabling only those that are active
        self.enableLastActiveControls()

        self.updateGraphicsView()

    def saveProjectConfig(self):
        configpath = self._view.setJSONDialog()
        if not configpath:
            return
        self._model.save_config(configpath)

    # cloud loading
    def analyze_pcap_fn(self, filename, progress_callback):
        self._model.setFilename(filename)
        self._pcap_frame_count = self._model.peek_size()

    def analyze_pcap(self):
        # disable controls
        self.finish_playing()
        #self._view.enableAllControls(False) # TODO: Should i block here?

        # ask for changes if file is loaded
        if self.pcap_filename is not None: 
            restart = self._view.getProjectRestartMessage()
            if not restart:
                return

        # get filename
        fname = self._view.getPCAPDialog()
        if not fname:
            return

        # activate status bar
        self._view.statusBar.showMessage("Counting frames ...")
        self._view.statusProgressBar.setVisible(True)
        self._view.statusProgressBar.setRange(0, 0)

        # peek how many frames there are
        self.pcap_filename = fname
        worker = Worker(self.analyze_pcap_fn, fname)
        worker.signals.finished.connect(self.load_frames)
        
        # Execute worker
        self.threadpool.start(worker)

    def load_frames(self):
        # restore status progress bar
        self._view.statusProgressBar.setVisible(False)
        self._view.statusProgressBar.setRange(0, 100)

        # using dialog window as how many frames would you like to load?
        settings, accepted = self._view.getInputDialog(
            max_frames=self._pcap_frame_count)
        if not accepted:
            print("[DEBUG] gon retur with status?")
            return

        self._loaded_frame_count = settings["to_frame"] - settings["from_frame"]

        # activate status bar
        self._view.statusBar.showMessage("Reading point cloud data ...")
        self._view.statusProgressBar.setVisible(True)

        # lock controls
        self._view.enableAllControls(False)

        # Pass the function to execute
        worker = Worker(self.load_frames_fn, settings["from_frame"], settings["to_frame"])
        worker.signals.progress.connect(self.frame_processing_progress)
        worker.signals.finished.connect(self.frame_loading_complete)
        self.threadpool.start(worker)

    def frame_processing_progress(self, n):
        self._view.statusProgressBar.setValue(n)

    def frame_loading_complete(self):
        self._view.statusBar.showMessage("")
        self._view.statusProgressBar.setValue(0)
        self._view.statusProgressBar.setVisible(False)

        # update scroller
        self.updateDataScrollers()
        # reset all processors
        self._model.resetProcessors()
        # reset dock parameters
        self._view.resetAllDocks()

        # enable locked view controls
        self.enableLastActiveControls()

        # for flexin visuals
        self.updateGraphicsView()

    def load_frames_fn(self, from_frame, to_frame, progress_callback):
        self._model.restartBuffering()
        self._model.resetFrameData()
        for n in range(to_frame):
            if n < from_frame:
                self._model.readNextFrame()
            else:
                self._model.loadFrame()

            progress_callback.emit((n+1)*100/(to_frame))

    # output

    def generate_output_fn(self, start_frame, end_frame, progress_callback):
        self._model.restartBuffering()
        for (n, ts, clusters, p) in self._model.processingGen(start_frame, end_frame):
            self.outputWritter.add(n, ts, clusters)
            progress_callback.emit(p)

    def generate_output(self):
        # stop player
        self.finish_playing()
        settings, accepted = self._view.getOutputDialog(max_frames=self._pcap_frame_count-1)
        if not accepted:
            print("[DEBUG] gon return")
            return

        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self._view, 'Save File','',"All Files (*)")
        if not fname:
            print("[DEBUG] gon return")
            return

        self.outputWritter = OutputWriter(fname,
            outputFormat=settings["params"]["file_format"])

        # activate status bar
        self._view.enableAllControls(False)
        self._view.statusBar.showMessage("Writting output ...")
        self._view.statusProgressBar.setVisible(True)

        # Pass the function to execute
        worker = Worker(self.generate_output_fn,
            settings["from_frame"], settings["to_frame"])
        worker.signals.progress.connect(self.output_writting_progress)
        worker.signals.finished.connect(self.output_writting_complete)
        
        # Execute worker
        self.threadpool.start(worker)

    def output_writting_progress(self, n):
        self._view.statusProgressBar.setValue(n)
        # also update ETA and i/n frames

    def output_writting_complete(self):
        self._view.statusBar.showMessage("")
        self._view.statusProgressBar.setValue(0)
        self._view.statusProgressBar.setVisible(False)
        self.outputWritter.close()

        # enabling only those that are active
        self.enableLastActiveControls()

    #
    # MODEL UPDATING
    #
    def _apply_preprocessing_fn(self, progress_callback):
        for p in self._model.updatePreprocessedGen():
            progress_callback.emit(p)

    def apply_preprocessing(self):
        # disable controls
        self.finish_playing()
        self._view.enableAllControls(False)
        self._view.statusBar.showMessage("Applying preprocessing ...")
        self._view.statusProgressBar.setVisible(True)

        # Pass the function to execute worker task
        worker = Worker(self._apply_preprocessing_fn)
        worker.signals.progress.connect(self.frame_processing_progress)
        worker.signals.finished.connect(self.frame_preprocessing_complete)
        self.threadpool.start(worker)

    def frame_preprocessing_complete(self):
        self._view.statusBar.showMessage("")
        self._view.statusProgressBar.setValue(0)
        self._view.statusProgressBar.setVisible(False)

        # enabling only those that are active
        self.enableLastActiveControls()

        # update graphics
        self.updateGraphicsView()

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
            self._model.createClusterer(method=settings["method"], **settings["params"])
            self.apply_clustering()
        else:
            self._model.destroyClusterer()
            self._view.enableTracking(False)
            self._view.enableOuput(False)
            self.previewClusters()

    def _apply_clustering_fn(self, progress_callback):
        for p in self._model.extractClustersGen():
            progress_callback.emit(p)

    def apply_clustering(self):
        # disable controls
        self.finish_playing()
        self._view.enableAllControls(False)
        self._view.statusBar.showMessage("Calculating clusters ...")
        self._view.statusProgressBar.setVisible(True)

        # Pass the function to execute worker task
        worker = Worker(self._apply_clustering_fn)
        worker.signals.progress.connect(self.frame_processing_progress)
        worker.signals.finished.connect(self.clustering_complete)
        print("[DEBUG] N active threads: {}".format(self.threadpool.activeThreadCount()))
        self.threadpool.start(worker)

    def clustering_complete(self):
        self._view.statusBar.showMessage("")
        self._view.statusProgressBar.setValue(0)
        self._view.statusProgressBar.setVisible(False)

         # enabling only those that are active
        self.enableLastActiveControls()

        self.previewClusters()

    #
    # TRACKING
    #
    
    def applyTracking(self):
        if self._view.trackingDock.enableProcessing.isChecked():
            settings = self._view.trackingDock.getSettings()
            self._model.createTracker(method=settings["method"], **settings["params"])
            self.apply_tracking()
        else:
            self._model.destroyTracker()
            self._view.enableOuput(False)
            self.previewClusters()

    def _apply_tracking_fn(self, progress_callback):
        for p in self._model.trackClustersGen():
            progress_callback.emit(p)

    def apply_tracking(self):
        # disable controls
        self.finish_playing()
        self._view.enableAllControls(False)
        self._view.statusBar.showMessage("Tracking clusters ...")
        self._view.statusProgressBar.setVisible(True)

        # TODO: block buttons

        # Pass the function to execute worker task
        worker = Worker(self._apply_tracking_fn)
        worker.signals.progress.connect(self.frame_processing_progress)
        worker.signals.finished.connect(self.tracking_complete)
        print("[DEBUG] N active threads: {}".format(self.threadpool.activeThreadCount()))
        self.threadpool.start(worker)

    def tracking_complete(self):
        self._view.statusBar.showMessage("")
        self._view.statusProgressBar.setValue(0)
        self._view.statusProgressBar.setVisible(False)

        # enabling only those that are active
        self.enableLastActiveControls()

        self.previewClusters()

    #
    # UI UPDATES
    #
    def frameChanged(self, idx):
        self._view.frameSpinBox.setValue(idx)
        self._view.frameSlider.setValue(idx)
        self._currentFrameIdx = idx
        self.updateGraphicsView()

    def updateDataScrollers(self):
        self._view.setMaxFrames(self._loaded_frame_count - 1)
        self._view.frameSlider.setMaximum(self._loaded_frame_count - 1)
        self._view.frameSlider.setValue(self._currentFrameIdx)
        self._view.frameSpinBox.setMaximum(self._loaded_frame_count - 1)
        self._view.frameSpinBox.setValue(self._currentFrameIdx)

    def frame_sequence_fn(self):
        if self._view.player_running and self._currentFrameIdx < self._loaded_frame_count - 1:
            self.frameChanged(self._currentFrameIdx + 1)
            QtCore.QTimer.singleShot(self._scrool_time, self.frame_sequence_fn)
        else:
            self.finish_playing()
            return
    
    def finish_playing(self):
        if self._view.player_running:
            self._view.switchPlayerState()

    def playFrameSequence(self):
        if self._view.player_running:
            QtCore.QTimer.singleShot(self._scrool_time, self.frame_sequence_fn)

    def moveFrameSequenceForward(self):
        self.frameChanged(self._loaded_frame_count - 1)

    def moveFrameSequenceBackward(self):
        self.frameChanged(0)
    
    def enableLastActiveControls(self):
        model_status = self._model.get_status()
                # enabling only those that are active
        self._view.enableFrameLoading(True)
        self._view.enableFrameControls(True)
        self._view.enableConfigLoading(True)
        self._view.enablePreprocessing(True)
        self._view.enableClustering(True)
        self._view.enableTracking(model_status["clustering"])
        self._view.enableOutput(model_status["tracking"])
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
