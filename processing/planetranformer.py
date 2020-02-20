import numpy as np
from scipy.spatial.transform import Rotation as R

class PlaneTransformer():
    def __init__(self, normal=None, intercept=None):
        self.normal = np.array(normal)
        self.intercept = intercept
        
    def get_plane_from_3_points(self, points):
        spoints = np.array(points)
        v1 = points[1,:] - points[0,:] 
        v2 = points[2,:] - points[0,:]
        n = np.cross(v1, v2)
        n = n if n[2] >= 0 else -n
        self.normal = n / np.linalg.norm(n)

        self.intercept = - np.dot(self.normal, points[0,:])

    def get_plane_coeff(self):
        return (self.normal, self.intercept)

    def get_config(self):
        return {
            "method": "3_points_plane", 
            "params": {
                "normal": self.normal.tolist(),
                "intercept": self.intercept
                }
            }

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