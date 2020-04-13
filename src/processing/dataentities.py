import numpy as np

class Packet:
    lasers = 32 # Number of lasers
    blocks = 12 # Number of firings in each packet
    eleLut = np.array( # Elevation look-up table
        [-30.67,-9.33,-29.33,
	 -8.00,-28.00,-6.66,
	 -26.66,-5.33,-25.33,
	 -4.00,-24.00,-2.67,
	 -22.67,-1.33,-21.33,
	 0.00,-20.00,1.33,
	 -18.67,2.67,-17.33,
	 4.00,-16.00,5.33,
	 -14.67,6.67,-13.33,
	 8.00,-12.00,9.33,
         -10.67,10.67])
    laserIds = np.arange(lasers)

    # Source for fast parsing:
    # https://stackoverflow.com/questions/36797088/speed-up-pythons-struct-unpakc
    def __init__(self, packet):
        self.azimuth = np.ndarray((Packet.blocks,), '<H', packet, 2, (100,))/100
        self.azimuth = np.repeat(self.azimuth,32).reshape(12,32)
        self.distance = np.ndarray((Packet.blocks,Packet.lasers),'<H', packet, 4, (100,3))*0.002
        self.intensity = np.ndarray((Packet.blocks,Packet.lasers),'<B', packet, 6, (100,3))

    def getFirings(self):
        i = 0
        while i < Packet.blocks:
            yield LaserFiring(Packet.laserIds,
                              Packet.eleLut,
                              self.azimuth[i],
                              self.distance[i],
                              self.intensity[i])
            i += 1
        
class LaserFiring:
    def __init__(self, id, elevation, azimuth, distance, intensity):
        self.id = id
        self.elevation = elevation
        self.azimuth = azimuth
        self.distance = distance
        self.intensity = intensity


class Frame:
    def __init__(self):
        size = 70000
        self.id = np.zeros(size)
        self.elevation = np.zeros(size)
        self.azimuth = np.zeros(size)
        self.distance = np.zeros(size)
        self.intensity = np.zeros(size)
        self.i = 0 # Current index
        self.x = None
        self.y = None
        self.z = None
        self.aziRad = None
        self.eleRad = None


    def radiansCheck(self):
        if(self.aziRad is None):
            self.aziRad = np.deg2rad(self.azimuth)
        if(self.eleRad is None):
            self.eleRad = np.deg2rad(self.elevation)
        

    def getXs(self):
        self.radiansCheck()
        if(self.x is None):
            self.x = (self.distance * np.cos(self.eleRad) * np.sin(self.aziRad)).flatten()
        return self.x
    
    def getYs(self):
        self.radiansCheck()
        if(self.y is None):
            self.y = (self.distance * np.cos(self.eleRad) * np.cos(self.aziRad)).flatten()
        return self.y
    
    def getZs(self):
        self.radiansCheck()
        if(self.z is None):
            self.z = (self.distance * np.sin(self.eleRad)).flatten()
        return self.z

    def getCartesian(self):
        self.radiansCheck()
        x = (self.distance * np.cos(self.eleRad) * np.sin(self.aziRad)).flatten()
        y = (self.distance * np.cos(self.eleRad) * np.cos(self.aziRad)).flatten()
        z = (self.distance * np.sin(self.eleRad)).flatten()
        return x,y,z

    def append(self,firing):
        nextI = self.i + Packet.lasers
        self.id[self.i:nextI] = firing.id
        self.elevation[self.i:nextI] = firing.elevation
        self.azimuth[self.i:nextI] = firing.azimuth
        self.distance[self.i:nextI] = firing.distance
        self.intensity[self.i:nextI] = firing.intensity
        self.i = nextI
        return self

    def finalize(self):
        self.id = self.id[:self.i]
        self.elevation = self.elevation[:self.i]
        self.azimuth = self.azimuth[:self.i]
        self.distance = self.distance[:self.i]
        self.intensity = self.intensity[:self.i]
        return self

    def save_csv(self, filename):
        # stack everything and save as CSV
        stacked = np.column_stack(
            (self.id, self.elevation, self.azimuth, self.distance, self.intensity))
        header = "id,elevation,azimuth,distance,intensity"
        fmt = ["%-10d","%-10.5f","%-10.5f","%-10.5f","%-10.5f"]
        np.savetxt(filename, stacked, delimiter="", header=header, fmt=fmt)

    def load_csv(self, filename):
        with open(filename, "r") as read_file:
            i, elev, az, dist, ints = np.loadtxt(
            read_file, delimiter=None, skiprows=1, unpack=True, max_rows=70000)

        self.id = i
        self.elevation = elev
        self.azimuth = az
        self.distance = dist
        self.intensity = ints
        self.radiansCheck()