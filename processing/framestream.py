from threading import Thread
import sys
from queue import Queue
from .pcapframeparser import PcapFrameParser

class FrameStream:
    def __init__(self, stream, queueSize=10):
        # initialize the file stream along with the boolean
        # used to indicate if the thread should be stopped or not
        self.stream = stream # frame generator
        self.stopped = False
 
        # initialize the queue used to store frames read from
        # the video file
        self.Q = Queue(maxsize=queueSize)

    def start(self):
        # start a thread to read frames from the file video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely
        while True:
            # if the thread indicator variable is set, stop the
            # thread
            if self.stopped:
                return
 
            # otherwise, ensure the queue has room in it
            if not self.Q.full():
                # try read the next frame from the file,
                # if nothing left, return
                try:
                    frame = next(self.stream)
                except StopIteration:
                    self.stop()
                    return
                self.Q.put(frame)

    def read(self):
        # return next frame in the queue
        return self.Q.get()

    def more(self):
        # return True if there are still frames in the queue
        return self.Q.qsize() > 0

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

    def preprocess(self, frame):
        x,y,z = frame.getCartesian()
        return (x,y,z)