import copy
import json
import numpy as np
from .pcapframeparser import PcapFrameParser
from .framestream import FrameStream
from .planetranformer import PlaneTransformer
from .cloudclipper import CloudClipper
from .backgroundextractor import BackgroundExtractor
from .backgroundsubtractor import BackgroundSubtractor

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
        self.bg_extractor = None
        self.backgroundFrame = None

    #
    # LOAD/SAVE config
    #
    def init_from_config(self, configpath):
        with open(configpath, "r") as read_file:
            config = json.load(read_file)

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

        # background subtractor
        # if bg subtractor is in config, initialize it:
        if "0000background_subtractor" in config.keys():
            # check if bg extractor or a cloud is configured
            bgconfig = config["background_subtractor"]
            # try to load cloud
            bg_path = bgconfig["background"]["path"]
            if os.path.exists(bg_path):
                pass
                # do stuff
            else:
                # if no path or invalid path, try to extract cloud
                self.bg_extractor = BackgroundExtractor(
                    **bgconfig["background"]["params"])
                self.bg_extractor.extract(self._originalFrames)
                self.backgroundFrame = self.bg_extractor.get_background()

            # finally create bg subtractor
            self.bg_subtractor = BackgroundSubtractor.factory(
                method=bgconfig["method"], bg_cloud=self.backgroundFrame,
                **bgconfig["params"])
        else:
            self.destroyBgExtractor()
            self.destroyBgSubtractor()

    def save_config(self, configpath):
        with open(configpath, "w") as write_file:

            config = {}
            if self.transformer is not None:
                settings = self.transformer.get_config()
                config["transformer"] = settings

            if self.clipper is not None:
                settings = self.clipper.get_config()
                config["clipper"] = settings

            if self.bg_subtractor is not None:
                settings = self.bg_subtractor.get_config()
                config["bg_subtractor"] = settings

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
    def createBgExtractor(self, method, **kwargs):
        pass

    def destroyBgExtractor(self):
        self.bg_extractor = None

    def createBgSubtractor(self, bg_cloud, method, **kwargs):
        pass

    def destroyBgSubtractor(self):
        self.bg_subtractor = None



