import numpy as np
from copy import deepcopy

class BackgroundExtractor:
    def __init__(self, percentile=80, non_zero=70, n_frames=100):
        self.numScanLines = 32
        self.frames = [1]
        self.percentile = percentile
        self.non_zero = non_zero
        self.n_frames = n_frames
        self.background = None

    def reshape2scanlines(self, arr):
        newSize = (int(len(arr)/self.numScanLines), self.numScanLines)
        return newSize, arr.reshape(newSize)
        
    def extract(self, frames):
        rangeImgs = []
        newSizes = []
        # Prepare range images
        for f in frames:
            newSize, rangeImg = self.reshape2scanlines(frames[f].distance)
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
        bgDist = np.percentile(stacked, self.percentile, axis=2)
        nonZero = np.count_nonzero(stacked, axis=2)
        zeroMask = nonZero < len(frames)*(self.non_zero/100)
        bgDist[zeroMask] = 0

        # Convert from spherical to cartesian coordinates
        xs = []
        ys = []
        zs = []
        for k,i in enumerate(self.frames):
            if(k > self.n_frames):
                break
            
            bgFrame = deepcopy(frames[i])
            bgFrame.distance = bgDist

            # Reshape azimuth and elevation arrays in accordance with size of distance array
            bgFrame.azimuth = self.reshape2scanlines(bgFrame.azimuth)[1]
            bgFrame.azimuth = bgFrame.azimuth[:imgHeight,:].flatten()
            bgFrame.elevation = self.reshape2scanlines(bgFrame.elevation)[1]
            bgFrame.elevation = bgFrame.elevation[:imgHeight,:].flatten()

            # Convert to cartesian coordinates
            aziRad = np.deg2rad(bgFrame.azimuth)
            eleRad = np.deg2rad(bgFrame.elevation)
            currX = (bgFrame.distance.flatten() * np.cos(eleRad) * np.sin(aziRad)).flatten()
            currY = (bgFrame.distance.flatten() * np.cos(eleRad) * np.cos(aziRad)).flatten()
            currZ = (bgFrame.distance.flatten() * np.sin(eleRad)).flatten()

            xs.append(currX)
            ys.append(currY)
            zs.append(currZ)
            
        # Prepare PCL PointCloud object with the points 
        x = np.array(xs).flatten()
        y = np.array(ys).flatten()
        z = np.array(zs).flatten()
        data = np.vstack((x,y,z)).astype(np.float32).T
        self.background = data
        return data

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

