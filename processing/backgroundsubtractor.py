import numpy as np
from scipy.spatial import cKDTree
from sklearn.neighbors import BallTree

class BackgroundSubtractor():
    @staticmethod
    def factory(method, bg_cloud, **kwargs):
        if method == "kd_tree":
            return KDTreeSubtractor(bg_cloud, **kwargs)
        elif method == "octree":
            return OctreeSubtractor(bg_cloud, **kwargs)
        else:
            ValueError(method)

class OctreeSubtractor():
    def __init__(self, bg_cloud, resolution):
        self.bg = bg_cloud
        self.bgTree = BallTree(bg_cloud.to_array(), leaf_size=10)
        p = pcl.PointCloud()
        self.cd = p.make_octreeChangeDetector(resolution)
    
    def getArray(self,x,y,z):
        # this operation belogs to FrameStream thread
        data = np.vstack((x,y,z)).astype(np.float32).T
        return np.unique(data.round(decimals=4), axis=0)

    def subtract(self, x, y, z):
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

    def get_config(self):
        return {
            "method": "octree", 
            "params": {
                "background": "",
                "resolution": self.resolution
                }
            }

class KDTreeSubtractor():
    def __init__(self, bg_cloud, search_radius=0.1):
        self.bgTree = BallTree(bg_cloud.to_array(), leaf_size=10)
        self.search_radius = search_radius

    def getArray(self,x,y,z):
        # this operation belogs to FrameStream thread
        data = np.vstack((x,y,z)).astype(np.float32).T
        return np.unique(data.round(decimals=4), axis=0)

    def subtract(self, x, y, z):
        inputArray = self.getArray(x,y,z)
        counts = self.bgTree.query_radius(inputArray,
            r=self.search_radius, count_only=True)
        xNew, yNew, zNew = inputArray[counts==0].T
        return xNew, yNew, zNew

    def get_config(self):
        return {
            "method": "kdtree", 
            "params": {
                "background": "",
                "rolerance": self.tolerance
                }
            }

    def dede(bg):
        from scipy.spatial import cKDTree

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
