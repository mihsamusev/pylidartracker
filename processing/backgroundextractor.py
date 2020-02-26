import numpy as np
from copy import deepcopy

class BackgroundExtractor:
    def __init__(self, percentile=0.80, non_zero=0.70, n_frames=100, cartesian=False):
        self.numScanLines = 32
        self.percentile = percentile
        self.non_zero = non_zero
        self.n_frames = n_frames
        self.cartesian = cartesian
        self.background = None

    def reshape2scanlines(self, arr):
        newSize = (int(len(arr)/self.numScanLines), self.numScanLines)
        return newSize, arr.reshape(newSize)
        
    def extract(self, frames):
        rangeImgs = []
        newSizes = []
        # Prepare range images
        for f in frames:
            newSize, rangeImg = self.reshape2scanlines(f.distance)
            rangeImgs.append(rangeImg)            
            newSizes.append(newSize[0])

        # Find optimal range image height
        imgHeight = int(np.percentile(newSizes,5))
        #print("Optimal image height: ",imgHeight)
        
        # Cut range image to size and prepare image stack
        stack = []
        for img in rangeImgs:
            if(img.shape[0] < imgHeight):
                #print("Frame ignored...")
                continue            
            stack.append(img[:imgHeight,:])
        stacked = np.dstack(stack)

        # Calc percentile and apply non-zero check
        bgDist = np.percentile(stacked, self.percentile * 100, axis=2)
        nonZero = np.count_nonzero(stacked, axis=2)
        zeroMask = nonZero < len(frames)*(self.non_zero)
        bgDist[zeroMask] = 0

        # Convert from spherical to cartesian coordinates
        bgFrame = deepcopy(frames[1])
        bgFrame.distance = bgDist.flatten()

        # Reshape azimuth and elevation arrays in accordance with size of distance array
        bgFrame.azimuth = self.reshape2scanlines(bgFrame.azimuth)[1]
        bgFrame.azimuth = bgFrame.azimuth[:imgHeight,:].flatten()
        bgFrame.elevation = self.reshape2scanlines(bgFrame.elevation)[1]
        bgFrame.elevation = bgFrame.elevation[:imgHeight,:].flatten()

        if self.cartesian:
            # Convert to cartesian coordinates
            aziRad = np.deg2rad(bgFrame.azimuth)
            eleRad = np.deg2rad(bgFrame.elevation)
            x = (bgFrame.distance * np.cos(eleRad) * np.sin(aziRad))
            y = (bgFrame.distance * np.cos(eleRad) * np.cos(aziRad))
            z = (bgFrame.distance * np.sin(eleRad)).flatten()

            data = np.vstack((x,y,z)).astype(np.float32).T
            self.background = data
        else:
            self.background = bgFrame


    def get_background(self):
        return self.background

    def get_config(self):
        return {
            "path": "",
            "method": "range_image", 
            "params": {
                "percentile": self.percentile,
                "non_zero": self.non_zero,
                "n_frames": self.n_frames
                }
            }

