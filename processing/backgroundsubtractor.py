import pcl
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.neighbors import BallTree

class BackgroundSubtractor:
    def __init__(self, bgCloud, resolution):
        self.bg = bgCloud
        self.bgTree = BallTree(bgCloud.to_array(), leaf_size=10)
        p = pcl.PointCloud()
        self.cd = p.make_octreeChangeDetector(resolution)
    
    def getArray(self,x,y,z):
        # this operation belogs to FrameStream thread
        data = np.vstack((x,y,z)).astype(np.float32).T
        return np.unique(data.round(decimals=4), axis=0)

    def process(self, x, y, z):
        data = self.getArray(x,y,z)
        p = pcl.PointCloud(data)
        self.cd.delete_tree()

        self.cd.set_input_cloud(self.bg)
        self.cd.add_points_from_input_cloud()
        self.cd.switchBuffers()
        self.cd.set_input_cloud(p)
        self.cd.add_points_from_input_cloud()
        res = self.cd.get_PointIndicesFromNewVoxels()
        xNew, yNew, zNew = data[res].T
        return xNew,yNew,zNew

    def process2(self, x, y, z, searchRadius=0.3):
        inputArray = self.getArray(x,y,z)
        counts = self.bgTree.query_radius(inputArray,
            r=searchRadius, count_only=True)
        xNew, yNew, zNew = inputArray[counts==0].T
        return xNew, yNew, zNew

    def dede(self):
        from scipy.spatial import cKDTree
        from Gui import Gui
        import pcl
        import numpy as np
        gui = Gui()

        # import back ground and a frame
        bgCloud = pcl.load("./background_big.pcd")
        bg = bgCloud.to_array()
        frameCloud = pcl.load("../data/frame19020.pcd")
        frame = frameCloud.to_array()

        # make sure there are no identical values (like zeros or nans)
        # to avoid segfault
        bg = np.unique(bg.round(decimals=4), axis=0)
        bgTree = cKDTree(bg)
        frameTree = cKDTree(frame)

        res = frameTree.query_ball_tree(bgTree, r=0.2)
        idx = [i for i,x in enumerate(res) if not x]
        x,y,z = frameTree.data[idx].T
        xBg,yBg,zBg = bgTree.data.T
        print("SHO?")
        # Plot extracted background

        gui.setGreenPoints([x,y,z])
        gui.setBluePoints([xBg,yBg,zBg])
        gui.draw()
        gui.app.exec_()