from PyQt5 import QtCore 
import numpy as np

class Controller():
    def __init__(self, view, model):
        self._view = view
        self._model = model
        self._connectSignals()
        self._currentFrameIdx = 0
        self._maxFrames = 0

        self.isLatestTransform = False

    def _connectSignals(self):
        # frame scrolling
        self._view.frameSlider.valueChanged.connect(self.frameChanged)
        self._view.frameSpinBox.valueChanged.connect(self.frameChanged)

        # MENUBAR
        self._view.openFileMenu.triggered.connect(self.loadFrames)
        self._view.saveConfigMenu.triggered.connect(self.saveProjectConfig)
        self._view.loadConfigMenu.triggered.connect(self.loadProjectConfig)

        # TOOLBAR
        # load 
        self._view.actionLoadPCAP.triggered.connect(self.loadFrames)
        
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

    #
    # I/O
    #
    def loadProjectConfig(self):
        configpath = self._view.getJSONDialog()
        if not configpath:
            return

        self._model.init_from_config(configpath)
        self._model.updatePreprocessed()
        
        self._view.set_from_config(configpath)
        
        self.updateGraphicsView()

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
            self._model.updatePreprocessed()
        else:
            self._view.transformDock.updateResult(None)
            self._model.destroyTransformer()
            self._model.updatePreprocessed()
            
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
            self._model.updatePreprocessed()
        else:
            self._view.clippingDock.reset()
            self._model.destroyClipper()
            self._model.updatePreprocessed()

        #update view and status bar
        self.updateGraphicsView()

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

    def updateStatusBar(self):
        info = "Transform is up to date" if self.isLatestTransform else "transform is outdated"
        self._view.statusBar.showMessage(info)
    
    #
    # GRAPHICS UPDATE
    #
    def updateRawPoints(self):
        (ts, pts) = self._model.getFrame(self._currentFrameIdx)
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
        self._view.graphicsView.draw()
