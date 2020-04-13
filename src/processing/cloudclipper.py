import numpy as np
from skimage.measure import points_in_poly

class CloudClipper():
    @staticmethod
    def factory(method, **kwargs):
        if method == "polar":
            return PolarClipper(**kwargs)
        elif method == "cartesian":
            return CartesianClipper(**kwargs)
        elif method == "polygon":
            return PolygonalClipper(**kwargs)
        else:
            ValueError(method)

class PolarClipper():
    def __init__(self, azimuth_range, 
        fov, distance_range, z_range, inverse=False):
        self.azimuth_range = azimuth_range
        self.fov = fov
        self.distance_range = distance_range
        self.z_range = z_range
        self.inverse = inverse

    def clip(self, data):
        # Not implemented
        return data

    def get_config(self):
        return {}

class CartesianClipper():
    def __init__(self, x_range, y_range,
        z_range, inverse=False):
        # verify ranges are sorted
        self.x_range = x_range
        self.y_range = y_range
        self.z_range = z_range
        self.inverse = inverse

    def clip(self, data):
        # verify that data is 3D

        # calculate masks for inliers in x, y and z ranges 
        x_mask = (data[:,0] > self.x_range[0]) and (data[:,0] < self.x_range[1])
        y_mask = (data[:,1] > self.y_range[0]) and (data[:,1] < self.y_range[1])
        z_mask = (data[:,2] > self.z_range[0]) and (data[:,2] < self.z_range[1])
        mask = x_mask & y_mask & z_mask

        # apply inversion if required
        if self.inverse:
            mask = np.invert(mask)

        return data[mask]

    def get_config(self):
        return {}

class PolygonalClipper():
    def __init__(self, polygon, z_range, inverse=False):
        # verify polygon is not self intersecting
        # z_range is sorted
        self.polygon = np.array(polygon)
        self.z_range = np.array(z_range)
        self.inverse = inverse

    def clip(self, data):
        # calculate mask for inliers of 2d polygon defined in XY
        # calculate maskf ro inliers in z range
        xy_mask = points_in_poly(data[:,:2], self.polygon)
        if self.z_range[0] == self.z_range[1]:
            z_mask = np.full((data.shape[0], ), True)
        else:
            z_mask = (data[:,2] > self.z_range[0]) & (data[:,2] < self.z_range[1])
        mask = xy_mask & z_mask
        
        # apply inversion if required
        if self.inverse:
            mask = np.invert(mask)

        return data[mask]

    def get_config(self):
            return {
            "method": "polygon", 
            "params": {
                "polygon": self.polygon.tolist(),
                "z_range": self.z_range.tolist(),
                "inverse": self.inverse
                }
            }
    

