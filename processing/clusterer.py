import numpy as np
from sklearn.cluster import AgglomerativeClustering, DBSCAN
from scipy.spatial import ConvexHull
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
        self.track = None


    def getCentroid(self):
        self.centroid = np.mean(self.points, axis=1)
        return self.centroid

    def getAABB(self, is_3d=True):
        xmax, ymax, zmax = np.max(self.points, axis=0)
        xmin, ymin, zmin = np.min(self.points, axis=0)

        if is_3d:
            polygon = np.array([
                [xmin, ymin, zmin],
                [xmax, ymin, zmin],
                [xmax, ymax, zmin],
                [xmin, ymax, zmin],
                [xmin, ymin, zmin],
                [xmin, ymin, zmax],
                [xmax, ymin, zmax],
                [xmax, ymax, zmax],
                [xmin, ymax, zmax],
                [xmin, ymin, zmax],
                [xmax, ymin, zmax],
                [xmax, ymin, zmin],
                [xmax, ymax, zmin],
                [xmax, ymax, zmax],
                [xmin, ymax, zmax],
                [xmin, ymax, zmin]
            ])
        else:
            polygon = np.array([
                [xmin, ymin, 0],
                [xmax, ymin, 0],
                [xmax, ymax, 0],
                [xmin, ymax, 0],
                [xmin, ymin, 0]
            ])
        return polygon

    def getOOBB(self, is_3d=True):
        # get convex hull of pounts projected to XY (remove z)
        xy_points = self.points[:,0:2]
        hull = ConvexHull(xy_points)

        # get counterclockwise indices, close the list with idx 0
        boundary = np.vstack((xy_points[hull.vertices,:], xy_points[hull.vertices[0],:]))
        # compute xyHull centroid
        
        hull_c = np.mean(xy_points, axis=0)
        # compute translations and rotations
        t_cs_to_origin = np.eye(4)
        t_cs_to_origin[0:2, 3] = - hull_c
        t_origin_to_cs = np.eye(4)
        t_origin_to_cs[0:2, 3] = hull_c

        # unknowns to find
        rotation_to_min_area_box = np.eye(4)
        minArea = 1e20
        b_min = None
        b_max = None

        for i in range(len(boundary) - 1):
            # get vectors along and across the i'th edge of the convex hull
            p0 = boundary[i,:]
            p1 = boundary[i+1,:]
            along = p1 - p0
            along = along / np.linalg.norm(along)

            # build rotation matrix to the coord system with basis
            # [along edge, ccw perp to edge]
            rotation = np.eye(4)
            rotation[0,0:3] = np.array([along[0], along[1], 0])
            rotation[1,0:3] = np.array([-along[1], along[0], 0])
            transform = rotation.dot(t_cs_to_origin)

            # transform polygon to i'th edge axis alligned
            expanded_boundary = np.hstack((boundary, np.ones((boundary.shape[0], 2)))) #TODO put OUTSIDE!
            aligned_boundary = transform.dot(expanded_boundary.T).T

            # calculate area of a
            aa_min = np.min(aligned_boundary, axis=0)
            aa_max = np.max(aligned_boundary, axis=0)
            area = (aa_max[0] - aa_min[0]) * (aa_max[1] - aa_min[0])
            print("Area is {}".format(area))
            if area < minArea:
                minArea = area
                rotation_to_min_area_box = rotation
                b_min = aa_min
                b_max = aa_max

        print("min area found: area: {} xy_min {} xy_max {}".format(minArea,aa_min[0:2],aa_max[0:2]))

        if is_3d:
            zmax = np.max(self.points[:,2])
            polygon = np.array([
                [b_min[0], b_min[1], 0],
                [b_max[0], b_min[1], 0],
                [b_max[0], b_max[1], 0],
                [b_min[0], b_max[1], 0],
                [b_min[0], b_min[1], 0],
                [b_min[0], b_min[1], zmax],
                [b_max[0], b_min[1], zmax],
                [b_max[0], b_max[1], zmax],
                [b_min[0], b_max[1], zmax],
                [b_min[0], b_min[1], zmax],
                [b_max[0], b_min[1], zmax],
                [b_max[0], b_min[1], 0],
                [b_max[0], b_max[1], 0],
                [b_max[0], b_max[1], zmax],
                [b_min[0], b_max[1], zmax],
                [b_min[0], b_max[1], 0]
            ])
        else:
            polygon = np.array([
                [b_min[0], b_min[1], 0],
                [b_max[0], b_min[1], 0],
                [b_max[0], b_max[1], 0],
                [b_min[0], b_max[1], 0],
                [b_min[0], b_min[1], 0]
            ])
        polygon = np.hstack((polygon, np.ones((polygon.shape[0], 1))))
        #turned_poly = (rotation_to_min_area_box.T.dot(polygon.T)).T
        expanded_points = np.hstack((self.points, np.ones((self.points.shape[0], 1))))
        turned_points = t_cs_to_origin.dot(expanded_points.T).T

        reverse_transform = rotation_to_min_area_box.T
        turned_poly = reverse_transform.dot(polygon.T).T
        translated_poly = t_origin_to_cs.dot(turned_poly.T).T

        return translated_poly[:,0:3]

class NaiveClustering():
    def __init__(self, search_radius=0.1, is_xy=False,
        min_samples=20, linkage="single"):
        self.search_radius = search_radius
        self.is_xy = is_xy
        self.dimensions = 2 if is_xy else 3
        self.min_samples = min_samples # TODO: NOT USED ANYWHERE
        self.clusterer = AgglomerativeClustering(
            n_clusters=None, distance_threshold=search_radius,
            linkage=linkage)

    def cluster(self, points):
        labels = self.clusterer.fit_predict(points[:,:self.dimensions])
        unique_labels = set(labels)

        clusters = []
        for k in unique_labels:
            cluster_mask = labels == k
            clusters.append(Cluster(points[cluster_mask]))
        return clusters

class DBSCANClustering():
    def __init__(self, search_radius=0.1, is_xy=False, 
        min_samples=20, multiprocess=False):
        #
        self.search_radius = search_radius
        self.is_xy = is_xy
        self.dimensions = 2 if is_xy else 3
        self.min_samples = min_samples
        self.multiprocess = -1 if multiprocess else None
        self.clusterer = DBSCAN(
            eps=search_radius, min_samples=min_samples,
            n_jobs=self.multiprocess)

    def cluster(self, points):
        if points.shape[0] == 0:
            return []

        labels = self.clusterer.fit_predict(points[:,:self.dimensions])
        unique_labels = set(labels)

        clusters = []
        for k in unique_labels:
            if k == -1:
                continue
            cluster_mask = labels == k
            clusters.append(Cluster(points[cluster_mask]))
        return clusters

