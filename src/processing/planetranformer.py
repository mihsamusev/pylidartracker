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
        r = self.get_rotation_matrix(self.normal, axisZ)
        data = r.apply(data).astype("float32")
        return data

    def rotate_to_new_x(self, data, vx):
        """
        rotate data around z axis so that new x direction matches vx 
        """
        axisX = np.array([1, 0, 0])
        # project vx to XY plane
        vx[2] = 0
        r = self.get_rotation_matrix(axisX, vx)
        data = r.apply(data).astype("float32")
        return data

    def translate_to(self, data, x, y, z):
        """
        Translate to a new origin being x,y,z
        """
        data -= np.array([x,y,z])
        return data

    def get_rotation_matrix(self, fromAxis, toAxis):
        """
        This function finds a rotation from quaternion
        that rotates one vector to the orientation of another
        """
        theta = np.arccos(np.dot(fromAxis, toAxis))
        rotAxis = np.cross(fromAxis, toAxis)
        rotAxis = rotAxis / np.linalg.norm(rotAxis)

        w = np.cos(theta / 2)
        x, y, z = np.sin(theta / 2) * rotAxis

        return R.from_quat([x,y,z,w])