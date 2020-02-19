import copy
import numpy as np
from .pcapframeparser import PcapFrameParser
from .framestream import FrameStream
from .triangleplanetranformer import TrianglePlaneTransformer
from .cloudclipper import CloudClipper

class LidarProcessor():
    def __init__(self):
        self.filename = None
        self._originalFrames = []
        self._preprocessedFrames = []
        self.bufferStarted = False
        self.frameGenerator = None
        self.frameBuffer = None

        self.transformer = None

        self.clipper = None
        
        self.bg_subtractor = None
        self.backgroundFrame = None

    #
    # I/O
    #
    def setFilename(self, filename):
        self.filename = filename

    def restartBuffering(self):
        if self.filename is None:
            return

        parser = PcapFrameParser(self.filename)
        self.frameGenerator = parser.generator()
        #if self.frameBuffer is not None:
            #self.frameBuffer.stop()
        #self.frameBuffer = FrameStream(self.frameGenerator).start()
        #self.bufferStarted = True

    def loadNFrames(self, N):
        self._originalFrames = []
        for i in range(N):
            (ts, f) = self.readNextFrame()
            pts = self.arrayFromFrame(f)
            self._originalFrames.append((ts, pts))
        self._preprocessedFrames = copy.deepcopy(self._originalFrames)

    def readNextFrame(self):
        try:
            out = next(self.frameGenerator)
        except StopIteration:
            out = (None, None)
        return out

    def getFrame(self,frameID):
        return self._preprocessedFrames[frameID]

    def revertToOriginal(self):
        # do nothing if clouds have not even been transformed
        self._preprocessedFrames = copy.deepcopy(self._originalFrames)

    def arrayFromFrame(self, frame):
        x,y,z = frame.getCartesian()
        pts = np.vstack((x,y,z)).astype(np.float32).T
        return pts

    # 
    # PREPROCESSING
    #
    def updatePreprocessed(self):
        # update plane and background

        # update preprocessed points
        # if transformer exists and HMMMM reakky? transform background

        # if clipper exists clip original background

        for (i, (ts, pts)) in enumerate(self._originalFrames):
            # apply transformer
            if self.transformer is not None:
                pts = self.transformer.transform(pts)
                print("[DEBUG] Transforming")
                
            # apply clipper
            if self.clipper is not None:
                pts = self.clipper.clip(pts)
                print("[DEBUG] Clipping")
            
            # apply bg subtractor
            if self.bg_subtractor is not None:
                pts = self.bg_subtractor.subtract(pts)
                print("[DEBUG] Subtracting")

            # update preproc frames
            self._preprocessedFrames[i] = (ts, pts)

    #
    # PLANE ESTIMATION
    #
    def destroyTransformer(self):
        self.transformer = None

    def createTransformer(self, pts):
            self.transformer = TrianglePlaneTransformer()
            self.transformer.set_points(pts)
            self.transformer.calculate_plane()

    def getPlaneCoeff(self):
        return self.transformer.get_plane_coeff()

    #
    # CLOUD CLIPPER
    #
    def createClipper(self, method, **kwargs):
        self.clipper = CloudClipper.factory(method, **kwargs)

    def destroyClipper(self):
        self.clipper = None

    #
    # BG SUBTRACTOR
    #
    def createSubtractor(self, bg_cloud, method, **kwargs):
        pass

    def destroyBgSubtractor(self):
        self.bg_subtractor = None


