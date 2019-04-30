"""Simulate a Map Reduce Scenario where timeout prevention is required.
In this simulation we are using an Optimizer created for map reduce scenarios.
This improves the distribution of the computation no matter how the interest is formated.

Scenario consists of two NFN nodes and a Client. Goal of the simulation is to add en

Client <--------> ICN1 <-*-----------> NFN1
                         \-----------> NFN2
                         \-----------> NFN3

"""

import abc
import queue
import unittest
import os
import schedule
import time

from PiCN.Layers.LinkLayer.Interfaces import SimulationBus
from PiCN.Layers.LinkLayer.Interfaces import AddressInfo
from PiCN.ProgramLibs.Fetch import Fetch
from PiCN.ProgramLibs.NFNForwarder import NFNForwarder
from PiCN.ProgramLibs.ICNForwarder import ICNForwarder
from PiCN.ProgramLibs.ICNDataRepository import ICNDataRepository
from PiCN.Layers.PacketEncodingLayer.Encoder import BasicEncoder, SimpleStringEncoder, NdnTlvEncoder
from PiCN.Packets import Content, Interest, Name
from PiCN.Mgmt import MgmtClient


class BalancedForwardingStrategySimulation(unittest.TestCase):
    """Test the forwarding strategy"""

    @abc.abstractmethod
    def get_encoder(self) -> BasicEncoder:
        return SimpleStringEncoder

    def setUp(self):
        self.encoder_type = self.get_encoder()
        self.simulation_bus = SimulationBus(packetencoder=self.encoder_type())

        self.fetch_tool1 = Fetch("icn1", None, 255, self.encoder_type(), interfaces=[self.simulation_bus.add_interface("fetchtool1")])

        self.icn1 = ICNForwarder(port=0, encoder=self.encoder_type(),
                                 interfaces=[self.simulation_bus.add_interface("icn1")], log_level=255,
                                 ageing_interval=1)
        self.nfn1 = NFNForwarder(port=0, encoder=self.encoder_type(),
                                 interfaces=[self.simulation_bus.add_interface("nfn1")], log_level=255,
                                 ageing_interval=1)
        self.nfn2 = NFNForwarder(port=0, encoder=self.encoder_type(),
                                 interfaces=[self.simulation_bus.add_interface("nfn2")], log_level=255,
                                 ageing_interval=1)
        self.nfn3 = NFNForwarder(port=0, encoder=self.encoder_type(),
                                 interfaces=[self.simulation_bus.add_interface("nfn3")], log_level=255,
                                 ageing_interval=1)

        c1 = Content(Name("/x/y"), "x..y")
        self.nfn1.mgmt.cs.add_content_object(c1)
        c2 = Content(Name("/a/b"), "a..b")
        self.nfn2.mgmt.cs.add_content_object(c2)
        c3 = Content(Name("/a/b"), "a..b")
        self.nfn3.mgmt.cs.add_content_object(c3)


        self.nfn1.icnlayer.pit.set_pit_timeout(0)
        self.nfn1.icnlayer.cs.set_cs_timeout(30)

        self.nfn2.icnlayer.pit.set_pit_timeout(0)
        self.nfn2.icnlayer.cs.set_cs_timeout(30)

        self.nfn3.icnlayer.pit.set_pit_timeout(0)
        self.nfn3.icnlayer.cs.set_cs_timeout(30)


        self.mgmt_client0 = MgmtClient(self.icn1.mgmt.mgmt_sock.getsockname()[1])
        self.mgmt_client1 = MgmtClient(self.nfn1.mgmt.mgmt_sock.getsockname()[1])
        self.mgmt_client2 = MgmtClient(self.nfn2.mgmt.mgmt_sock.getsockname()[1])
        self.mgmt_client3 = MgmtClient(self.nfn3.mgmt.mgmt_sock.getsockname()[1])


    def tearDown(self):
        self.icn1.stop_forwarder()
       # self.nfn1.stop_forwarder()
        self.fetch_tool1.stop_fetch()
        self.simulation_bus.stop_process()
        #self.tearDown_repo()


    def setup_faces_and_connections(self):
        self.icn1.start_forwarder()
        self.nfn1.start_forwarder()
        self.nfn2.start_forwarder()
        self.nfn3.start_forwarder()
        self.simulation_bus.start_process()

        time.sleep(3)

        # setup forwarding rules
        self.mgmt_client0.add_face("nfn1", None, 0)
        self.mgmt_client0.add_forwarding_rule(Name("/x"), [0])
        self.mgmt_client0.add_face("nfn2", None, 0)
        self.mgmt_client0.add_forwarding_rule(Name("/a"), [1])
        self.mgmt_client0.add_face("nfn3", None, 0)
        self.mgmt_client0.add_forwarding_rule(Name("/a"), [2])
#
        #
        # #setup function code
        # self.mgmt_client0.add_new_content(Name("/lib/reduce4"),
        #                                   "PYTHON\nreduce4\ndef reduce4(a,b,c,d):\n     return a+b+c+d")
        # self.mgmt_client1.add_new_content(Name("/lib/func1"),
        #                                   "PYTHON\nf\ndef f(a):\n    for i in range(0,100000000):\n        a.upper()\n    return a.upper()")
        # self.mgmt_client2.add_new_content(Name("/lib/func2"),
        #                                   "PYTHON\nf\ndef f(a):\n    for i in range(0,100000000):\n        a.upper()\n    return a.upper()")
        # self.mgmt_client3.add_new_content(Name("/lib/func3"),
        #                                   "PYTHON\nf\ndef f(a):\n    for i in range(0,100000000):\n        a.upper()\n    return a.upper()")
        # self.mgmt_client4.add_new_content(Name("/lib/func4"),
        #                                   "PYTHON\nf\ndef f(a):\n    for i in range(0,100000000):\n        a.upper()\n    return a.upper()")


    # def setup_repo(self):
    #     for i in range(1,5):
    #         self.path = "/tmp/repo" + str(i)
    #         try:
    #             os.stat(self.path)
    #         except:
    #             os.mkdir(self.path)
    #         with open(self.path + "/data" + str(i), 'w+') as content_file:
    #             content_file.write("data" + str(i))
    #
    # def tearDown_repo(self):
    #     try:
    #         shutil.rmtree(self.path)
    #         os.remove("/tmp/repo")
    #     except:
    #         pass

    def test_simple_FS(self):
        """Simple map reduce test with input data as string parameter"""
        self.setup_faces_and_connections()

        name1 = Name("/x/y")
        name2 = Name("/a/b")
        res1 = self.fetch_tool1.fetch_data(name1, timeout=0)
        res2 = self.fetch_tool1.fetch_data(name2, timeout=0)
        time.sleep(3)
        print(res1)
        print(res2)
        self.assertEqual("x..y", res1)
        self.assertEqual("a..b", res2)

    #
    # def test_simple_map_reduce_data_from_repo(self):
    #     """Simple map reduce test with input data from repo"""
    #     self.setup_repo()
    #     self.setup_faces_and_connections()
    #
    #     name = Name("/lib/reduce4")
    #     name += '_(/lib/func1(/repo/r1/data1),/lib/func2(/repo/r2/data2),/lib/func3(/repo/r3/data3),/lib/func4(/repo/r4/data4))'
    #     name += "NFN"
    #
    #     res = self.fetch_tool1.fetch_data(name, timeout=0)
    #     time.sleep(3)
    #     print(res)
    #     self.assertEqual("DATA1DATA2DATA3DATA4", res)
    #
    #
    # def test_simple_map_reduce_data_from_repo_to_data(self):
    #     """Simple map reduce test with input data from repo forwarding to data"""
    #     self.setup_repo()
    #     self.setup_faces_and_connections()
    #
    #     name = Name("/repo/r1/data1")
    #     name += '/lib/reduce4(/lib/func1(_),/lib/func2(/repo/r2/data2),/lib/func3(/repo/r3/data3),/lib/func4(/repo/r4/data4))'
    #     name += "NFN"
    #
    #     res = self.fetch_tool1.fetch_data(name, timeout=0)
    #     time.sleep(3)
    #     print(res)
    #     self.assertEqual("DATA1DATA2DATA3DATA4", res)