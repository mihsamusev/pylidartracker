from struct import unpack
import dpkt
from .dataentities import Packet,LaserFiring,Frame
import numpy as np

class PcapFrameParser:
    def __init__(self, pcap_file):
        # check if PCAP file is really .pcap
        self.pcap_file = pcap_file
        self.packetStream = dpkt.pcap.Reader(open(self.pcap_file, 'rb'))
        self.frameCount = 0
        self.lastAzi = -1
        self.frame = Frame()

    def is_correct_port(self, buffer, port=2368):
        # get destination port from the UDP header
        dport = unpack(">H",buffer[36:38])[0]
        return  dport == port

    def generator(self):
        for ts, buf in self.packetStream:
            if(len(buf) != 1248):
                continue
            if not self.is_correct_port(buf, port=2368):
                continue

            payload = buf[42:]
            res = Packet(payload).getFirings()
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

    def peek_size(self):
        prev_max_rot = 0
        n = 0
        for _, buffer in self.packetStream:
            if len(buffer) != 1248:
                continue

            if not self.is_correct_port(buffer, port=2368):
                continue

            rot = np.ndarray((12,), '<H', buffer, 42+2, (100,))
            min_rot = rot[0]
            max_rot = rot[11]
            if max_rot < min_rot or prev_max_rot > min_rot:
                n += 1
            prev_max_rot = max_rot

        return n
