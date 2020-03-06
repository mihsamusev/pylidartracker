import numpy as np
from sklearn.cluster import AgglomerativeClustering, DBSCAN

class Clusterer():
    @staticmethod
    def factory(method, **kwargs):
        if method == "naive":
            return NaiveClustering(**kwargs)
        elif method == "dbscan":
            return DBSCANClustering(**kwargs)
        else:
            ValueError(method)

class Cluster():
    def __init__(self, points):
        self.points = points
        self.size = points.shape[0]
        self.centroid = None
        self.bounding_box = None


    def getCentroid(self):
        pass

    def getBounds(self):
        xmax, ymax, zmax = np.max(self.points, axis=0)
        xmin, ymin, zmin = np.min(self.points, axis=0)
        return np.array([xmin, xmax, ymin, ymax, zmin, zmax])

    def fitBoundingBox(self, method="min_area_box"):
        self.bounding_box = BoundingBox.fit_box(method)

class BoundingBox():
    @staticmethod
    def fit_box(points, method="min_area_box"):
        pass

class NaiveClustering():
    def __init__(self, search_radius=0.1, dimensions=3):
        self.search_radius = search_radius
        self.dimensions = dimensions
        self.clusterer = AgglomerativeClustering(
            n_clusters=None, distance_threshold=search_radius, linkage="complete")

    def cluster(self, points):
        labels = self.clusterer.fit_predict(points[:,0:self.dimensions-1])
        unique_labels = set(labels)

        clusters = []
        for k in unique_labels:
            cluster_mask = labels == k
            clusters.append(Cluster(points[cluster_mask]))
        return clusters

class DBSCANClustering():
    def __init__(self, search_radius=0.1, dimensions=3, 
        min_samples=20, multiprocess=False):
        #
        self.search_radius = search_radius
        self.dimensions = dimensions
        self.min_samples = min_samples
        self.multiprocess = -1 if multiprocess else None
        self.clusterer = DBSCAN(
            eps=search_radius, min_samples=min_samples,
            n_jobs=self.multiprocess)

    def cluster(self, points):
        if points.shape[0] == 0:
            return []

        labels = self.clusterer.fit_predict(points[:,0:self.dimensions-1])
        unique_labels = set(labels)

        clusters = []
        for k in unique_labels:
            if k == -1:
                continue
            cluster_mask = labels == k
            clusters.append(Cluster(points[cluster_mask]))
        return clusters

