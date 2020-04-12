import numpy as np
from scipy.spatial import cKDTree
from sklearn.neighbors import BallTree

class BackgroundSubtractor():
    @staticmethod
    def factory(method, **kwargs):
        if method == "kd_tree":
            return KDTreeSubtractor(**kwargs)
        elif method == "octree":
            return OctreeSubtractor(**kwargs)
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
    def __init__(self, bg_cloud=None, search_radius=0.1):
        self.bg_cloud = bg_cloud
        
        self.bgTree = None
        if self.bg_cloud is not None:
            self.bgTree = BallTree(bg_cloud, leaf_size=10)

        self.search_radius = search_radius

    def set_background2(self, bg_cloud):
        self.bg_cloud = bg_cloud
        self.bgTree = cKDTree(bg_cloud)

    def set_background(self, bg_cloud):
        self.bg_cloud = bg_cloud
        self.bgTree = BallTree(bg_cloud, leaf_size=10)

    def subtract2(self, arr):
        arrayTree = cKDTree(arr)
        res = arrayTree.query_ball_tree(
            self.bgTree, r=self.search_radius)
        idx = [i for i,x in enumerate(res) if not x]
        return arrayTree.data[idx]

    def subtract(self, arr):
        counts = self.bgTree.query_radius(arr,
            r=self.search_radius, count_only=True)
        return arr[counts==0]

    def get_config(self):
        return {
            "method": "kd_tree", 
            "params": {
                "search_radius": self.search_radius
                }
            }
