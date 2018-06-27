"""A ICN Repository using PiCN"""

import multiprocessing

from PiCN.LayerStack.LayerStack import LayerStack
from PiCN.Layers.ChunkLayer import BasicChunkLayer
from PiCN.Layers.PacketEncodingLayer import BasicPacketEncodingLayer
from PiCN.Layers.RepositoryLayer import BasicRepositoryLayer

from PiCN.Layers.ChunkLayer.Chunkifyer import SimpleContentChunkifyer
from PiCN.Layers.LinkLayer import BasicLinkLayer
from PiCN.Layers.LinkLayer.FaceIDTable import FaceIDDict
from PiCN.Layers.LinkLayer.Interfaces import UDP4Interface
from PiCN.Processes.PiCNSyncDataStructFactory import PiCNSyncDataStructFactory
from PiCN.Layers.PacketEncodingLayer.Encoder import SimpleStringEncoder
from PiCN.Layers.PacketEncodingLayer.Encoder import BasicEncoder
from PiCN.Layers.RepositoryLayer.Repository import SimpleFileSystemRepository
from PiCN.Logger import Logger
from PiCN.Packets import Name
from PiCN.Mgmt import Mgmt

# ----------------------------------------------------------------------

class ICNDataRepository(object):
    """A ICN Forwarder using PiCN"""

    def __init__(self, foldername: str, prefix: Name,
                 port=9000, log_level=255, encoder: BasicEncoder = None):

        logger = Logger("ICNRepo", log_level)
        logger.info("Start PiCN Data Repository")

        #packet encoder
        if encoder == None:
            self.encoder = SimpleStringEncoder(log_level = log_level)
        else:
            encoder.set_log_level(log_level)
            self.encoder = encoder
        #chunkifyer
        self.chunkifyer = SimpleContentChunkifyer()

        #repo
        self.repo = SimpleFileSystemRepository(foldername, prefix, logger)

        #initialize layers
        synced_data_struct_factory = PiCNSyncDataStructFactory()
        synced_data_struct_factory.register("faceidtable", FaceIDDict)
        synced_data_struct_factory.create_manager()
        faceidtable = synced_data_struct_factory.manager.faceidtable()

        interface = UDP4Interface(port)

        self.linklayer = BasicLinkLayer(interface, faceidtable, log_level=log_level)
        self.packetencodinglayer = BasicPacketEncodingLayer(self.encoder, log_level=log_level)
        self.chunklayer = BasicChunkLayer(self.chunkifyer, log_level=log_level)
        self.repolayer = BasicRepositoryLayer(self.repo, log_level=log_level)

        self.lstack: LayerStack = LayerStack([
            self.repolayer,
            self.chunklayer,
            self.packetencodinglayer,
            self.linklayer
        ])

        # mgmt
        self.mgmt = Mgmt(None, None, None, self.linklayer, self.linklayer.interfaces[0].get_port(),
                         self.start_repo, repo_path=foldername,
                         repo_prfx=prefix, log_level=log_level)

    def start_repo(self):
        # start processes
        self.lstack.start_all()
        self.mgmt.start_process()

    def stop_repo(self):
        #Stop processes
        self.lstack.stop_all()
        self.lstack.close_all()
        self.mgmt.stop_process()

# eof
