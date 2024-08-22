from mininet.topo import Topo
from mininet.link import TCLink
import os

class TopoFIUBAFTP(Topo):
    def __init__(self, **params):
        nConnections = int(os.getenv('nConnections', 3))
        nLose = int(os.getenv('nLose', 10))
        Topo.__init__(self, **params)

        server = self.addHost('server')

        switch = self.addSwitch('s1')

        self.addLink(server, switch, loss=nLose)
        for i in range(nConnections):
            new_host = self.addHost("h{}".format(i+1))
            self.addLink(switch, new_host, loss=nLose, cls=TCLink)

topos = {'fiuba-ftp-topo': TopoFIUBAFTP}