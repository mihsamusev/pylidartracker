import dpkt
import time
import numpy as np
import pandas as pd
from .dataentities import Packet,LaserFiring,Frame

class PcapFrameParser:
    def __init__(self, pcapFile):
        self.packetStream = dpkt.pcap.Reader(open(pcapFile, 'rb'))
        self.frameCount = 0
        self.lastAzi = -1
        self.frame = Frame()

    def generator(self):
        for ts, buf in self.packetStream:
            if(len(buf) != 1248):
                continue
            eth = dpkt.ethernet.Ethernet(buf)
            ip = eth.data
            udp = ip.data

            if(udp.dport != 2368):
                continue

            res = Packet(udp.data).getFirings()
            for firing in res:
                # Yield complete frames and create new Frame() container
                if(self.lastAzi > firing.azimuth[-1]):
                    self.frame.finalize()
                    yield (ts, self.frame)
                    self.frame = Frame()

                try: 
                    self.frame.append(firing)
                except:
                    pass
                
                # update last seen azimuth
                self.lastAzi = firing.azimuth[-1]



    

            
            

