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

        # load action
        self._view.actionLoadPCAP.triggered.connect(self.loadFrames)
        
        # transform action
        self._view.actionTransform.triggered.connect(
            self._view.showTransformDock)
        self._view.transformDock.pickBtn.toggled.connect(
            self.allowSelection)
        self._view.graphicsView.threePointsPicked.connect(
            self.calculateTransform)
        self._view.transformDock.displayPoints.stateChanged.connect(
            self.showSelectedPoints)
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
    # PLANE FITTING AND TRANSFORM ACTON
    #
    def showSelectedPoints(self):
        if self._view.transformDock.displayPoints.isChecked():
            self._view.graphicsView.setSelectedVisible(True)
        else:
            self._view.graphicsView.setSelectedVisible(False)

    def allowSelection(self):
        if self._view.transformDock.pickBtn.isChecked():
            # update dock
            self._view.transformDock.pickBtn.setText("Stop point picking")
            self._view.transformDock.displayPoints.setChecked(True)
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
        self._model.createTransformer(pts)

        # draw reults on widget and plane on the screen
        coeff = self._model.getPlaneCoeff()
        self._view.transformDock.updateResult(coeff)
        
        self._view.transformDock.pickBtn.setChecked(False)

    def applyTransform(self):
        if self._view.transformDock.enableTransform.isChecked():
            self._model.updatePreprocessed()
        else:
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
        self._model.createClipper(method="polygonal", **settings["params"])

        if settings["transform"]:
            self._model.updatePreprocessed()
        else:
            self._model.destroyClipper()
            self._model.updatePreprocessed()

        #update view and status bar
        self.updateGraphicsView()
    #
    # I/O
    #
    def loadFrames(self):
        fname = self._view.getFileFromOpenDialog()
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
        print(settings)
        if settings["display"]:
            self._view.graphicsView.setCropBox(polygon=settings["params"]["polygon"],
                zrange=settings["params"]["z_range"])
        else:
            self._view.graphicsView.setCropBox(polygon=None, zrange=None)
        self._view.graphicsView.draw()

    def updateGraphicsView(self):
        self.updateRawPoints()
        self._view.graphicsView.draw()
