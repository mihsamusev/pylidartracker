import copy
import json
import numpy as np
import time
from .pcapframeparser import PcapFrameParser
from .framestream import FrameStream
from .planetranformer import PlaneTransformer
from .cloudclipper import CloudClipper
from .backgroundextractor import BackgroundExtractor
from .backgroundsubtractor import BackgroundSubtractor
from .dataentities import Frame
from .clusterer import Clusterer

class LidarProcessor():
    def __init__(self):
        self.filename = None
        self._originalFrames = []
        self._timestamps = []
        self._preprocessedArrays = []
        self.bufferStarted = False
        self.frameGenerator = None
        self.frameBuffer = None

        self.transformer = None

        self.clipper = None
        
        self.bg_subtractor = None
        self.bg_extractor = None
        self.bg_filename = None
        self.originalBgFrame = None
        self.preprocessedBgArray = None

        self.clusterer = None
        self.frameClusters = []
    #
    # LOAD/SAVE config
    #
    def init_from_config(self, configpath):
        with open(configpath, "r") as read_file:
            config = json.load(read_file)

        # need validator for the config file to check if all necessary fields
        # are there and spelled correctly

        # call processors one by one
        # transformer
        if "transformer" in config.keys():
            self.createTransformer(**config["transformer"]["params"])
        else:
            self.destroyTransformer()

        # clipper
        if "clipper" in config.keys():
            self.createClipper(method=config["clipper"]["method"], 
                **config["clipper"]["params"])
        else:
            self.destroyClipper()

        # background cloud and subtractor
        if "background" in config.keys():
            if "path" in config["background"]:
                # try to get background cloud by loading file
                bg_path = config["background"]["path"]
                self.loadBackground(bg_path)

            elif "extractor" in config["background"]:
                # if no path or invalid path, try to extract cloud
                self.extractBackground(
                    method=config["background"]["extractor"]["method"],
                    **config["background"]["extractor"]["params"])

            # finally create bg subtractor
            if "subtractor" in config["background"]:
                self.createBgSubtractor(
                    method=config["background"]["subtractor"]["method"],
                    **config["background"]["subtractor"]["params"])
        else:
            self.destroyBgExtractor()
            self.destroyBgSubtractor()

    def save_config(self, configpath):
        with open(configpath, "w") as write_file:

            config = {}
            # transformer pre-processor part
            if self.transformer is not None:
                settings = self.transformer.get_config()
                config["transformer"] = settings

            # clipper pre-processor part
            if self.clipper is not None:
                settings = self.clipper.get_config()
                config["clipper"] = settings

            # background pre-processor part
            config["background"] = {}
            if self.bg_filename is not None:
                config["background"]["path"] = self.bg_filename
            else:
                config["background"]["path"] = ""

            if self.bg_extractor is not None:
                settings = self.bg_extractor.get_config()
                config["background"]["extractor"] = settings

            if self.bg_subtractor is not None:
                settings = self.bg_subtractor.get_config()
                config["background"]["subtractor"] = settings

            # TODO: clusterer part
            # TODO: tracker part
            # TODO: result definition part

            json.dump(config, write_file, indent=4)
            print("Config saved to:\n{0}".format(configpath))


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
            self._timestamps.append(ts)
            self._originalFrames.append(f)

            # preprocessed frames are the cartesian xyz arrays
            pts = self.arrayFromFrame(f)
            self._preprocessedArrays.append(pts)

    def readNextFrame(self):
        try:
            out = next(self.frameGenerator)
        except StopIteration:
            out = (None, None)
        return out

    def getTimestamp(self, frameID):
        return self._timestamps[frameID]

    def getArray(self,frameID):
        return self._preprocessedArrays[frameID]

    def arrayFromFrame(self, frame):
        x,y,z = frame.getCartesian()
        pts = np.vstack((x,y,z)).astype(np.float32).T
        pts = self.removeZeros(pts)
        return pts

    # 
    # PREPROCESSING
    #
    def updatePreprocessed(self):
        # ensure the subtractor is initiated with the correct
        # background point cloud
        if self.originalBgFrame is not None:
            pts = self.arrayFromFrame(self.originalBgFrame)
            self.preprocessedBgArray = self.preprocessBg(pts)
            if self.bg_subtractor is not None:
                self.bg_subtractor.set_background(self.preprocessedBgArray)

        # update preprocessed points
        self._preprocessedArrays = []
        for (i, frame) in enumerate(self._originalFrames):
            start = time.time()
            pts = self.arrayFromFrame(frame)
            pts = self.preprocessArray(pts)
            self._preprocessedArrays.append(pts)

            # timing
            print(f"[DEBUG] pre-processing frame{i+1}/{len(self._originalFrames)} in {time.time() - start} s")



    def preprocessArray(self, arr):
        # apply transformer
        if self.transformer is not None:
            arr = self.transformer.transform(arr)
            
        # apply clipper
        if self.clipper is not None:
            arr = self.clipper.clip(arr)

        # apply bg subtractor
        if self.bg_subtractor is not None:
            arr = self.bg_subtractor.subtract(arr)

        return arr

    def preprocessBg(self, arr):
        # apply transformer
        if self.transformer is not None:
            arr = self.transformer.transform(arr)
            
        # apply clipper
        if self.clipper is not None:
            arr = self.clipper.clip(arr)

        return arr

    def removeZeros(self, arr):
        return arr[np.all(arr, axis=1)]
    #
    # PLANE ESTIMATION
    #
    def destroyTransformer(self):
        self.transformer = None

    def createTransformer(self, points=None, **kwargs):
            if points is not None:
                self.transformer = PlaneTransformer()
                self.transformer.get_plane_from_3_points(points)
            elif "normal" in kwargs and "intercept" in kwargs:
                self.transformer = PlaneTransformer(
                    kwargs["normal"], kwargs["intercept"])
            else:
                ValueError("")

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
    # BG SUBTRACTOR / EXTRACTOR
    #
    def saveBackground(self, filename):
        if self.originalBgFrame is not None:
            self.originalBgFrame.save_csv(filename)
            self.bg_filename = filename

    def loadBackground(self, filename):
        self.bg_extractor = None
        self.originalBgFrame = Frame()
        self.originalBgFrame.load_csv(filename)
        self.bg_filename = filename
        
        pts = self.arrayFromFrame(self.originalBgFrame)
        self.preprocessedBgArray = self.preprocessArray(pts)

    def extractBackground(self, method, **kwargs):
        self.bg_extractor = BackgroundExtractor(**kwargs)
        self.bg_extractor.extract(self._originalFrames)
        self.originalBgFrame = self.bg_extractor.get_background()
        #
        pts = self.arrayFromFrame(self.originalBgFrame)
        self.preprocessedBgArray = self.preprocessArray(pts)

    def destroyBgExtractor(self):
        self.bg_extractor = None
        self.originalBgFrame = None
        self.preprocessedBgArray = None

    def createBgSubtractor(self, method, **kwargs):
        if self.originalBgFrame is not None:
            self.bg_subtractor = BackgroundSubtractor.factory(method, **kwargs)

    def destroyBgSubtractor(self):
        self.bg_subtractor = None

    #
    # CLUSTERER
    #
    def getClusters(self, frameID):
        if self.frameClusters:
            return self.frameClusters[frameID]
        else:
            return []

    def extractClusters(self, method, **kwargs):
        self.clusterer = Clusterer.factory(method, **kwargs)
        self.frameClusters = []
        for i, arr in enumerate(self._preprocessedArrays):
            clusters = self.clusterer.cluster(arr)
            self.frameClusters.append(clusters)
            print(f"[DEBUG][CLUSTERING] got {len(clusters)} clusters for frame {i}")

    def destroyClusterer(self):
        self.frameClusters = []
        self.clusterer = None

