import numpy as np
from scipy.spatial.transform import Rotation as R

class TrianglePlaneTransformer():
    def __init__(self, points=None):
        self.points = points
        self.normal = None
        self.intercept = None
        
    def calculate_plane(self):
        self.points = np.array(self.points)
        v1 = self.points[1,:] - self.points[0,:] 
        v2 = self.points[2,:] - self.points[0,:]
        n = np.cross(v1, v2)
        n = n if n[2] >= 0 else -n
        self.normal = n / np.linalg.norm(n)

        self.intercept = - np.dot(self.normal, self.points[0,:])


    def set_points(self, points):
        self.points = points

    def set_normal(self, normal):
        self.normal = normal

    def set_intercept(self, intercept):
        self.intercept = intercept

    def get_plane_coeff(self):
        return np.hstack((self.normal, self.intercept))
    # check collinearity
 
    # vector 0-1, vector 0-2
    # cross / normalize / ensure positive

    # calculate intercept from normal and a point

    def transform(self, data):
        if self.normal is None or self.intercept is None:
            raise ValueError("normal and intercept are not calcualted")
            
        # translate
        data = np.add(data, self.intercept * self.normal)

        # rotate
        axisZ = np.array([0, 0, 1])
        q = self.getQuaternion(self.normal, axisZ)
        data = q.apply(data).astype("float32")
        return data

    def getQuaternion(self, norm, axis):
        theta = np.arccos(np.dot(norm, axis))
        rotAxis = np.cross(norm, axis)
        rotAxis = rotAxis / np.linalg.norm(rotAxis)

        w = np.cos(theta / 2)
        x, y, z = np.sin(theta / 2) * rotAxis

        return R.from_quat([x,y,z,w])