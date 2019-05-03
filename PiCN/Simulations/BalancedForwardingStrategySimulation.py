"""Simulate a Map Reduce Scenario where timeout prevention is required.
In this simulation we are using an Optimizer created for map reduce scenarios.
This improves the distribution of the computation no matter how the interest is formated.

Scenario consists of two NFN nodes and a Client. Goal of the simulation is to add en

Client <--------> NFN0 <-*-----------> NFN1 <-----------> Repo1
                         \-----------> NFN2 <-----------> Repo2
                         \-----------> NFN3 <-----------> Repo3
                         \-----------> NFN4 <-----------> Repo4
"""

import abc
import queue
import unittest
import os
import shutil
import time
import _thread
import threading

from PiCN.Layers.LinkLayer.Interfaces import SimulationBus
from PiCN.Layers.LinkLayer.Interfaces import AddressInfo
from PiCN.Layers.NFNLayer.NFNOptimizer import MapReduceOptimizer
from PiCN.ProgramLibs.Fetch import Fetch
from PiCN.ProgramLibs.NFNForwarder import NFNForwarder
from PiCN.ProgramLibs.ICNForwarder import ICNForwarder

from PiCN.ProgramLibs.ICNDataRepository import ICNDataRepository
from PiCN.Layers.PacketEncodingLayer.Encoder import BasicEncoder, SimpleStringEncoder, NdnTlvEncoder
from PiCN.Packets import Content, Interest, Name
from PiCN.Mgmt import MgmtClient

class Fs_thread(threading.Thread):
    def __init__(self, name: Name, fetch_tool):
        threading.Thread.__init__(self)
        self.name = name
        self.fetch_tool = fetch_tool
    def run(self):
        self.request_function()

    def request_function(self):
        self.fetch_tool.fetch_data(self.name)


class Initiation(unittest.TestCase):
    """Simulate a Map Reduce Scenario where timeout prevention is required."""

    @abc.abstractmethod
    def get_encoder(self) -> BasicEncoder:
        return SimpleStringEncoder

    def setUp(self):
        self.encoder_type = self.get_encoder()
        self.simulation_bus = SimulationBus(packetencoder=self.encoder_type())

        self.fetch_tool1 = Fetch("nfn0", None, 255, self.encoder_type(), interfaces=[self.simulation_bus.add_interface("fetchtool1")])

        self.nfn0 = NFNForwarder(port=0, encoder=self.encoder_type(),
                                 interfaces=[self.simulation_bus.add_interface("nfn0")], log_level=255,
                                 ageing_interval=3)
        self.nfn1 = NFNForwarder(port=0, encoder=self.encoder_type(),
                                 interfaces=[self.simulation_bus.add_interface("nfn1")], log_level=255,
                                 ageing_interval=3)
        self.nfn2 = NFNForwarder(port=0, encoder=self.encoder_type(),
                                 interfaces=[self.simulation_bus.add_interface("nfn2")], log_level=255,
                                 ageing_interval=3)
        self.nfn3 = NFNForwarder(port=0, encoder=self.encoder_type(),
                                 interfaces=[self.simulation_bus.add_interface("nfn3")], log_level=255,
                                 ageing_interval=3)
        self.nfn4 = NFNForwarder(port=0, encoder=self.encoder_type(),
                                 interfaces=[self.simulation_bus.add_interface("nfn4")], log_level=255,
                                 ageing_interval=3)

        self.repo1 = ICNDataRepository("/tmp/repo1", Name("/repo/r1"), 0, 255, self.encoder_type(), False, False,
                                       [self.simulation_bus.add_interface("repo1")])
        self.repo2 = ICNDataRepository("/tmp/repo2", Name("/repo/r2"), 0, 255, self.encoder_type(), False, False,
                                       [self.simulation_bus.add_interface("repo2")])
        self.repo3 = ICNDataRepository("/tmp/repo3", Name("/repo/r3"), 0, 255, self.encoder_type(), False, False,
                                       [self.simulation_bus.add_interface("repo3")])
        self.repo4 = ICNDataRepository("/tmp/repo4", Name("/repo/r4"), 0, 255, self.encoder_type(), False, False,
                                       [self.simulation_bus.add_interface("repo4")])

        self.nfn1.icnlayer.pit.set_pit_timeout(0)
        self.nfn1.icnlayer.cs.set_cs_timeout(30)
        self.nfn2.icnlayer.pit.set_pit_timeout(0)
        self.nfn2.icnlayer.cs.set_cs_timeout(30)
        self.nfn3.icnlayer.pit.set_pit_timeout(0)
        self.nfn3.icnlayer.cs.set_cs_timeout(30)
        self.nfn4.icnlayer.pit.set_pit_timeout(0)
        self.nfn4.icnlayer.cs.set_cs_timeout(30)


        self.mgmt_client0 = MgmtClient(self.nfn0.mgmt.mgmt_sock.getsockname()[1])
        self.mgmt_client1 = MgmtClient(self.nfn1.mgmt.mgmt_sock.getsockname()[1])
        self.mgmt_client2 = MgmtClient(self.nfn2.mgmt.mgmt_sock.getsockname()[1])
        self.mgmt_client3 = MgmtClient(self.nfn3.mgmt.mgmt_sock.getsockname()[1])
        self.mgmt_client4 = MgmtClient(self.nfn4.mgmt.mgmt_sock.getsockname()[1])

    def tearDown(self):
        self.nfn0.stop_forwarder()
        self.nfn1.stop_forwarder()
        self.nfn2.stop_forwarder()
        self.nfn3.stop_forwarder()
        self.nfn4.stop_forwarder()
        self.repo1.stop_repo()
        self.repo2.stop_repo()
        self.repo3.stop_repo()
        self.repo4.stop_repo()
        self.fetch_tool1.stop_fetch()
        self.simulation_bus.stop_process()
        self.tearDown_repo()

    def setup_faces_and_connections(self):
        self.nfn0.start_forwarder()
        self.nfn1.start_forwarder()
        self.nfn2.start_forwarder()
        self.nfn3.start_forwarder()
        self.nfn4.start_forwarder()

        self.repo1.start_repo()
        self.repo2.start_repo()
        self.repo3.start_repo()
        self.repo4.start_repo()

        self.simulation_bus.start_process()

        time.sleep(3)

        # setup forwarding rules
        self.mgmt_client0.add_face("nfn1", None, 0)
        self.mgmt_client0.add_forwarding_rule(Name("/lib/func1"), [0])
        self.mgmt_client0.add_face("nfn2", None, 0)
        self.mgmt_client0.add_forwarding_rule(Name("/lib/func2"), [1])
        self.mgmt_client0.add_face("nfn2", None, 0)
        self.mgmt_client0.add_forwarding_rule(Name("/lib/func1"), [1])
        self.mgmt_client0.add_face("nfn3", None, 0)
        self.mgmt_client0.add_forwarding_rule(Name("/lib/func3"), [2])
        self.mgmt_client0.add_face("nfn3", None, 0)
        self.mgmt_client0.add_forwarding_rule(Name("/lib/func1"), [2])
        self.mgmt_client0.add_face("nfn4", None, 0)
        self.mgmt_client0.add_forwarding_rule(Name("/lib/func4"), [3])

        self.mgmt_client1.add_face("repo1", None, 0)
        self.mgmt_client1.add_forwarding_rule(Name("/repo/r1"), [0])
        self.mgmt_client2.add_face("repo2", None, 0)
        self.mgmt_client2.add_forwarding_rule(Name("/repo/r2"), [0])
        self.mgmt_client3.add_face("repo3", None, 0)
        self.mgmt_client3.add_forwarding_rule(Name("/repo/r3"), [0])
        self.mgmt_client4.add_face("repo4", None, 0)
        self.mgmt_client4.add_forwarding_rule(Name("/repo/r4"), [0])


        self.mgmt_client1.add_face("nfn0", None, 0)
        self.mgmt_client1.add_forwarding_rule(Name("/lib"), [1])
        self.mgmt_client2.add_face("nfn0", None, 0)
        self.mgmt_client2.add_forwarding_rule(Name("/lib"), [1])
        self.mgmt_client3.add_face("nfn0", None, 0)
        self.mgmt_client3.add_forwarding_rule(Name("/lib"), [1])
        self.mgmt_client4.add_face("nfn0", None, 0)
        self.mgmt_client4.add_forwarding_rule(Name("/lib"), [1])

        #setup function code
        #self.mgmt_client1.add_new_content(Name("/lib/func1"),"PYTHON\nf\ndef f(n):\n return n")
        self.mgmt_client1.add_new_content(Name("/lib/func1"), "PYTHON\nf\ndef f(n):\n  result =[]\n  x,y =0,1\n  while x<n:\n    result.append(x)\n    x,y = y, y+x\n  return result")
        self.mgmt_client2.add_new_content(Name("/lib/func1"), "PYTHON\nf\ndef f(n):\n  result =[]\n  x,y =0,1\n  while x<n:\n    result.append(x)\n    x,y = y, y+x\n  return result")
        self.mgmt_client2.add_new_content(Name("/lib/func2"),"func2")
        self.mgmt_client3.add_new_content(Name("/lib/func1"), "PYTHON\nf\ndef f(n):\n  result =[]\n  x,y =0,1\n  while x<n:\n    result.append(x)\n    x,y = y, y+x\n  return result")
        self.mgmt_client4.add_new_content(Name("/lib/func4"),"func4")

        # self.mgmt_client1.add_new_content(Name("/lib/func1"),
        #                                   "PYTHON\nf\ndef f():\n    for i in range(0,100000000):\n        a.upper()\n    return a.upper()")
        # self.mgmt_client2.add_new_content(Name("/lib/func2"),
        #                                   "PYTHON\nf\ndef f(a):\n    for i in range(0,100000000):\n        a.upper()\n    return a.upper()")
        # self.mgmt_client3.add_new_content(Name("/lib/func3"),
        #                                   "PYTHON\nf\ndef f(a):\n    for i in range(0,100000000):\n        a.upper()\n    return a.upper()")
        # self.mgmt_client4.add_new_content(Name("/lib/func4"),
        #                                   "PYTHON\nf\ndef f(a):\n    for i in range(0,100000000):\n        a.upper()\n    return a.upper()")
        #

    def setup_repo(self):
        for i in range(1,5):
            self.path = "/tmp/repo" + str(i)
            try:
                os.stat(self.path)
            except:
                os.mkdir(self.path)
            with open(self.path + "/data" + str(i), 'w+') as content_file:
                content_file.write("data" + str(i))

    def tearDown_repo(self):
        try:
            shutil.rmtree(self.path)
            os.remove("/tmp/repo")
        except:
            pass

    def test_simple_Fs(self):
        self.setup_repo()
        self.setup_faces_and_connections()
        name1 = Name("/lib/func1")
        name1 += '_(100000000000000000000000000)'
        name1 += "NFN"

        name2 = Name("/lib/func1")
        name2 += '_(20000000000000000000000)'
        name2 += "NFN"

        name3 = Name("/lib/func1")
        name3 += '_(30000000)'
        name3 += "NFN"
        t1= Fs_thread(name1, fetch_tool= self.fetch_tool1)
        t2= Fs_thread(name2, fetch_tool= self.fetch_tool1)
        t3= Fs_thread(name3, fetch_tool= self.fetch_tool1)

        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()

    # def first_request(self):
    #         name1 = Name("/lib/func1")
    #         name1 += '_(100000000000000000000000000)'
    #         name1 += "NFN"
    #         self.fetch_tool1.fetch_data(name1, timeout=10)
    #
    # def second_request(self):
    #         name1 = Name("/lib/func1")
    #         name1 += '_(5)'
    #         name1 += "NFN"
    #         self.fetch_tool1.fetch_data(name1, timeout=10)
    #
    # def third_request(self):
    #         name1 = Name("/lib/func1")
    #         name1 += '_(1000000)'
    #         name1 += "NFN"
    #         self.fetch_tool1.fetch_data(name1, timeout=10)
    #
    # def test_simple_Fs(self):
    #     """Simple FS test"""
    #     self.setup_repo()
    #     self.setup_faces_and_connections()
    #     t1= threading.Thread(self.first_request())
    #     t2= threading.Thread(self.second_request())
    #     t3= threading.Thread(self.third_request())
    #     t1.start()
    #     t2.start()
    #     t3.start()


        # t1 = threading.Thread(self.first_request())
        # t2 = threading.Thread(self.second_request())
        # t3 = threading.Thread(self.third_request())
        # t1.start()
        # t2.start()
        # t3.start()

        #
        # name2= Name("/lib/func1")
        # name2 += '_(5)'
        # name2 += "NFN"
        #
        # res1 = self.
        # res2 = self.fetch_tool1.fetch_data(name2, timeout=0)
        # print(res1)
        # print(res2)
       # self.assertEqual("func1", res1)

        # res2 = self.fetch_tool1.fetch_data(name2, timeout=0)
        # time.sleep(3)
        # print(res2)
        # self.assertEqual("func2", res2)

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