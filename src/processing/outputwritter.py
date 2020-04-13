import os 
import json

class OutputWriter:
    def __init__(self, outputPath, outputFormat="json", bufSize=1000):
    # verify that file doesnt exist
        if os.path.exists(outputPath):
            #os.remove(outputPath)
            with open(outputPath, "w") as f:
                f.write("")
            #raise ValueError("Specified path to file already exists", outputPath)
    
    # initialize outputfile
        self.outputFile = open(outputPath, 'a')

        # create buffer
        self.buffer = []
        self.bufSize = bufSize
        self.startIdx = 0

        self.format = outputFormat
        if self.format.lower() == "json":
            self.serializer = OutputWriter.serialize_json
        elif self.format.lower() == "csv":
            self.serializer = OutputWriter.serialize_csv
        else:
            raise  ValueError("Wrong output format, should be 'json' or 'csv'",
                outputFormat)

    @staticmethod
    def serialize_json(n, ts, clusters):
        payload = {
            "frame_number": n,
            "timestamp": ts,
            "objects": [c.get_json() for c in clusters]
            }
        string = json.dumps(payload)
        return string

    @staticmethod
    def serialize_csv(n, ts, clusters):
        # TODO: NB! outputs empty str if clusters are empty
        string_array = ["{:<8}, {:<20}, {}".format(
            n, ts, c.get_json()) for c in clusters]
        string = "\n".join(string_array)
        return string

    def add(self, n, ts, clusters):
        serialized = self.serializer(n, ts, clusters)
        # add data to buffer, if buffer is full flush it to 
        # the database
        self.buffer.extend([serialized])

        if len(self.buffer) >= self.bufSize:
            self.flush()

    def flush(self):
        # calculate the inserting range to hdf5 database for the buffer 
        endIdx = self.startIdx + len(self.buffer)
        buffer_string = "\n".join(self.buffer)+"\n"
        self.outputFile.write(buffer_string)

        # update start and reset buffer
        self.startIdx = endIdx
        self.buffer = []

    def close(self):
        if len(self.buffer) > 0:
            self.flush()
        self.outputFile.close()

if __name__ == "__main__":
    import time

    n_rows = 100000
    # test1
    start = time.time()
    ow = OutputWriter("./textpath2", outputFormat="csv", bufSize=1000)
    for i in range(n_rows):
        ow.add(i, start, [])
    ow.close()
    end = time.time()
    print("[TEST1] finished in {} seconds".format(end- start))
