# import the necessary packages
from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np

class Tracker():
    @staticmethod
    def factory(method, **kwargs):
        if method == "nearest_neigbour":
            return CentroidTracker(**kwargs)
        else:
            ValueError(method)

# from pyimagesearch
# https://www.pyimagesearch.com/2018/07/23/simple-object-tracking-with-opencv/
class CentroidTracker():
    def __init__(self, max_missing=50):
        self.nextObjectID = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.max_missing = max_missing
        self.inputMapping = {}
    def register(self, centroid):
        # when registering an object we use the next available object
        # ID to store the centroid
        self.objects[self.nextObjectID] = centroid
        self.disappeared[self.nextObjectID] = 0
        self.nextObjectID += 1

    def deregister(self, objectID):
        # to deregister an object ID we delete the object ID from
        # both of our respective dictionaries
        del self.objects[objectID]
        del self.disappeared[objectID]

    def update(self, inputCentroids):
        self.inputMapping = {}
        # if list of new objects is empty increment existing objects
        # dissapear count, deregister if expired, return early
        if len(inputCentroids) == 0:
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > self.max_missing:
                    self.deregister(objectID)
            return self.objects

        # if we are currently not tracking any objects take the input
        # centroids and register each of them
        if len(self.objects) == 0:
            for i in range(0, len(inputCentroids)):
                self.inputMapping[i] = self.nextObjectID
                self.register(inputCentroids[i])

        # otherwise, are are currently tracking objects so we need to
        # try to match the input centroids to existing object
        # centroids
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())
            # TODO: here comes a kalman filter prediction of the next position
            # for the object centroids, the next position is used to
            # match the input centroids

            # compute the distance matrix
            D = dist.cdist(np.array(objectCentroids), inputCentroids)
            
            # sort rows by index of smallest value. Get columns with
            # smallest values at those rows. We have ordered pair of
            # indices for smallest distances.
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            # keep track of rows (currentObj) and colums (newObj) we have examined
            usedRows = set()
            usedCols = set()
            for (row, col) in zip(rows, cols):
                # if we have already examined either the row or
                # column value before, ignore it
                # val
                if row in usedRows or col in usedCols:
                    continue
                # otherwise, grab the object ID for the current row,
                # set its new centroid, and reset the disappeared
                # counter

                # TODO: Here can verify either if the object is within
                # Kalman filter uncertainty, or if the direaction is matching

                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]
                self.inputMapping[col] = objectID
                self.disappeared[objectID] = 0
                # indicate that we have examined each of the row and
                # column indexes, respectively
                usedRows.add(row)
                usedCols.add(col)

            # compute both the row and column index we have NOT yet
            # examined
            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            # in the event that the number of object centroids is
            # equal or greater than the number of input centroids
            # we need to check and see if some of these objects have
            # potentially disappeared
            if D.shape[0] >= D.shape[1]:
                # loop over the unused row indexes
                for row in unusedRows:
                    # grab the object ID for the corresponding row
                    # index and increment the disappeared counter
                    objectID = objectIDs[row]
                    self.disappeared[objectID] += 1
                    # check to see if the number of consecutive
                    # frames the object has been marked "disappeared"
                    # for warrants deregistering the object
                    if self.disappeared[objectID] > self.max_missing:
                        self.deregister(objectID)

            # otherwise, if the number of input centroids is greater
            # than the number of existing object centroids we need to
            # register each new input centroid as a trackable object
            else:
                for col in unusedCols:
                    self.inputMapping[col] = self.nextObjectID
                    self.register(inputCentroids[col])

        # return the set of trackable objects
        return self.objects

    def getInputMapping(self):
        return self.inputMapping

    def printInputMapping(self):
        for k,v in self.inputMapping.items():
            print("Input object {} with centroid {} gets ID {}".format(v, self.objects[k], k))

    def debugObjects(self):
        for k,v in self.objects.items():
            print("Object: {}, centroid {}, missing {}".format(k, v, self.disappeared[k]))


if __name__ == "__main__":
    class TestObject:
        def __init__(self, centroid):
            self.centroid = np.array(centroid)
            self.id = None
        def __repr__(self):
            return "TestObject with centroid {} and id {}".format(self.centroid, self.id)

    ct = CentroidTracker(max_missing=1)
    inputObjects = [
        [TestObject([1.0, 1.0, 0.0]),
        TestObject([0.0, 0.2, 0.0]),
        TestObject([0.0, 02.0, 3.0]),
        ],
        [],
        [],
        [TestObject([1.0, 1.0, 0.0]),
        TestObject([0.0, 0.0, 0.0])
        ],
        [TestObject([0.3, 0.0, 0.0])
        ],
        [TestObject([1.2, 0.0, 0.0]),
        TestObject([3.0, 3.0, 0.0]),
        TestObject([1.5, 1.5, 0.0])
        ],
        [TestObject([3.1, 2.9, 0.0])
        ],
        [TestObject([2.5, 2.5, 0.0])
        ],
        [TestObject([0, 0, 0.0]),
        TestObject([2.5, 2.0, 0.0])
    ]]

    for i, newObj in enumerate(inputObjects):
        centroids = [o.centroid for o in newObj]
        ct.update(centroids)
        print("round ", i)
        mapping = ct.getInputMapping()
        for j, obj in enumerate(newObj):
            obj.id = mapping[j]
            print(obj)