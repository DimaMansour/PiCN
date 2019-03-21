"""Test the Basic ICN Layer implementation"""

import multiprocessing
import time
import unittest

from PiCN.Layers.ICNLayer import BasicICNLayer
from PiCN.Layers.ICNLayer.ContentStore import ContentStoreMemoryExact
from PiCN.Layers.ICNLayer.ForwardingInformationBase import ForwardingInformationBaseMemoryPrefix
from PiCN.Layers.ICNLayer.PendingInterestTable import PendingInterstTableMemoryExact
from PiCN.Packets import Name, Interest, Content, Nack, NackReason
from PiCN.Processes import PiCNSyncDataStructFactory


class test_BasicICNLayer(unittest.TestCase):
    """Test the Basic ICN Layer implementation"""

    def setUp(self):

        #setup icn_layer
        self.icn_layer = BasicICNLayer(log_level=255)

        synced_data_struct_factory = PiCNSyncDataStructFactory()
        synced_data_struct_factory.register("cs", ContentStoreMemoryExact)
        synced_data_struct_factory.register("fib", ForwardingInformationBaseMemoryPrefix)
        synced_data_struct_factory.register("pit", PendingInterstTableMemoryExact)
        synced_data_struct_factory.create_manager()

        cs = synced_data_struct_factory.manager.cs()
        fib = synced_data_struct_factory.manager.fib()
        pit = synced_data_struct_factory.manager.pit()
        cs.set_cs_timeout(2)
        pit.set_pit_timeout(2)
        pit.set_pit_retransmits(2)

        self.icn_layer.cs = cs
        self.icn_layer.fib = fib
        self.icn_layer.pit = pit

        #setup queues icn_routing layer
        self.queue1_icn_routing_up = multiprocessing.Queue()
        self.queue1_icn_routing_down = multiprocessing.Queue()

        #add queues to ICN layer
        self.icn_layer.queue_from_lower = self.queue1_icn_routing_up
        self.icn_layer.queue_to_lower = self.queue1_icn_routing_down

    def tearDown(self):
        self.icn_layer.stop_process()

    def test_ICNLayer_interest_forward_basic(self):
        """Test ICN layer with no CS and PIT entry"""
        self.icn_layer.start_process()

        to_faceid = 1
        from_faceid = 2

        #Add entry to the fib
        name = Name("/test/data")
        interest = Interest("/test/data")
        self.icn_layer.fib.add_fib_entry(name, [to_faceid], static=True)

        #forward entry
        self.queue1_icn_routing_up.put([from_faceid, interest])
        try:
            faceid, data = self.queue1_icn_routing_down.get(timeout=2.0)
        except:
            self.fail()

        #check output
        self.assertEqual(faceid, to_faceid)
        self.assertEqual(data, interest)

        #check data structures
        self.assertEqual(self.icn_layer.cs.get_container_size(), 0)
        self.assertEqual(self.icn_layer.fib.get_container_size(), 1)
        self.assertEqual(self.icn_layer.pit.get_container_size(), 1)
        self.assertEqual(self.icn_layer.fib.find_fib_entry(name).faceid, [to_faceid])
        self.assertEqual(self.icn_layer.fib.find_fib_entry(name).name, name)
        self.assertEqual(self.icn_layer.pit.find_pit_entry(name).faceids[0], from_faceid)
        self.assertEqual(self.icn_layer.pit.find_pit_entry(name).name, name)

    def test_ICNLayer_interest_forward_longest_match(self):
        """Test ICN layer with no CS and no PIT entry and longest match"""
        self.icn_layer.start_process()

        to_face_id = 1
        from_face_id = 2

        #Add entry to the fib
        name = Name("/test")
        interest = Interest("/test/data")
        self.icn_layer.fib.add_fib_entry(name, [to_face_id], static=True)

        #forward entry
        self.queue1_icn_routing_up.put([from_face_id, interest])
        try:
            face_id, data = self.queue1_icn_routing_down.get(timeout=2.0)
        except:
            self.fail()

        #check output
        self.assertEqual(face_id, to_face_id)
        self.assertEqual(data, interest)

        #check data structures
        self.assertEqual(self.icn_layer.cs.get_container_size(), 0)
        self.assertEqual(self.icn_layer.fib.get_container_size(), 1)
        self.assertEqual(self.icn_layer.pit.get_container_size(), 1)
        self.assertEqual(self.icn_layer.fib.find_fib_entry(name).faceid, [to_face_id])
        self.assertEqual(self.icn_layer.fib.find_fib_entry(name).name, name)
        self.assertEqual(self.icn_layer.pit.find_pit_entry(interest.name).faceids[0], from_face_id)
        self.assertEqual(self.icn_layer.pit.find_pit_entry(interest.name).name, interest.name)

    def test_ICNLayer_interest_forward_deduplication(self):
        """Test ICN layer with no CS and no PIT entry and deduplication"""
        self.icn_layer.start_process()

        to_face_id = 1
        from_face_id_1 = 2
        from_face_id_2 = 3

        # Add entry to the fib
        name = Name("/test")
        interest1 = Interest("/test/data")
        interest2 = Interest("/test/data")
        self.icn_layer.fib.add_fib_entry(name, [to_face_id])

        # forward entry
        self.queue1_icn_routing_up.put([from_face_id_1, interest1])
        try:
            face_id, data = self.queue1_icn_routing_down.get(timeout=2.0)
        except:
            self.fail()

        self.queue1_icn_routing_up.put([from_face_id_2, interest2], block=True)
        self.assertTrue(self.queue1_icn_routing_down.empty())

        time.sleep(3)

        # check output
        self.assertEqual(face_id, to_face_id)
        self.assertEqual(data, interest1)

        time.sleep(0.3) # sleep required, since there is no blocking get before the checks
        # check data structures
        self.assertEqual(self.icn_layer.cs.get_container_size(), 0)
        self.assertEqual(self.icn_layer.fib.get_container_size(), 1)
        self.assertEqual(self.icn_layer.pit.get_container_size(), 1)
        self.assertEqual(self.icn_layer.fib.find_fib_entry(name).faceid, [to_face_id])
        self.assertEqual(self.icn_layer.fib.find_fib_entry(name).name, name)
        self.assertEqual(len(self.icn_layer.pit.find_pit_entry(interest1.name).faceids), 2)
        self.assertEqual(self.icn_layer.pit.find_pit_entry(interest1.name).faceids, [from_face_id_1, from_face_id_2])
        self.assertEqual(self.icn_layer.pit.find_pit_entry(interest1.name).name, interest1.name)

    def test_ICNLayer_interest_forward_content_match(self):
        """Test ICN layer with CS entry matching"""
        self.icn_layer.start_process()

        from_face_id = 2
        interest = Interest("/test/data")

        #add content
        content = Content("/test/data")
        self.icn_layer.cs.add_content_object(content)

        #request content
        self.queue1_icn_routing_up.put([from_face_id, interest])

        #get content
        try:
            face_id, data = self.queue1_icn_routing_down.get(timeout=2.0)
        except:
            self.fail()

        self.assertEqual(data, content)
        self.assertEqual(face_id, from_face_id)

    def test_ICNLayer_interest_forward_content_no_match(self):
        """Test ICN layer with CS entry no match"""
        self.icn_layer.start_process()

        to_face_id = 1
        from_face_id = 2
        interest = Interest("/test/data/bla")
        name = Name("/test/data")
        self.icn_layer.fib.add_fib_entry(name, [to_face_id], static=True)

        #add content
        content = Content("/test/data")
        self.icn_layer.cs.add_content_object(content)

        #request content
        self.queue1_icn_routing_up.put([from_face_id, interest])

        #get data from fib
        try:
            face_id, data = self.queue1_icn_routing_down.get(timeout=2.0)
        except:
            self.fail()

        self.assertTrue(data, interest)
        self.assertTrue(face_id, to_face_id)
        self.assertTrue(self.queue1_icn_routing_up.empty())
        self.assertEqual(self.icn_layer.pit.get_container_size(), 1)
        self.assertEqual(self.icn_layer.pit.find_pit_entry(interest.name).name, interest.name)

    def test_ICNLayer_content_no_pit(self):
        """Test receiving a content object with no PIT entry"""
        self.icn_layer.start_process()
        from_face_id = 2
        content = Content("/test/data")
        self.queue1_icn_routing_up.put([from_face_id, content])

        self.assertTrue(self.queue1_icn_routing_down.empty())

    def test_ICNLayer_content_pit(self):
        """Test receiving a content object with PIT entry"""
        self.icn_layer.start_process()
        content_in_face_id = 1
        from_face_id = 2
        name = Name("/test/data")
        content = Content("/test/data")

        self.icn_layer.pit.add_pit_entry(name, from_face_id, content_in_face_id, None, None)

        self.queue1_icn_routing_up.put([content_in_face_id, content])

        try:
            face_id, data = self.queue1_icn_routing_down.get(timeout=2.0)
        except:
            self.fail()

        self.assertEqual(face_id, from_face_id)
        self.assertEqual(data, content)

    def test_ICNLayer_content_two_pit_entries(self):
        """Test receiving a content object with two PIT entries"""
        self.icn_layer.start_process()
        content_in_face_id = 1
        from_face_id_1 = 2
        from_face_id_2 = 3
        name = Name("/test/data")
        content = Content("/test/data")

        self.icn_layer.pit.add_pit_entry(name, from_face_id_1, content_in_face_id, None, False)
        self.icn_layer.pit.add_pit_entry(name, from_face_id_2, content_in_face_id, None, False)

        self.queue1_icn_routing_up.put([content_in_face_id, content])

        try:
            face_id_1, data1 = self.queue1_icn_routing_down.get(timeout=2.0)
        except:
            self.fail()

        self.assertEqual(face_id_1, from_face_id_1)
        self.assertEqual(data1, content)

        face_id_2, data2 = self.queue1_icn_routing_down.get()

        self.assertEqual(face_id_2, from_face_id_2)
        self.assertEqual(data2, content)

    def test_ICNLayer_ageing_pit(self):
        """Test PIT ageing"""

        self.icn_layer.start_process()
        from_face_id_1 = 1
        to_face_id = 2
        name = Name("/test/data")
        interest = Interest(name)

        self.icn_layer.fib.add_fib_entry(name, [to_face_id])
        self.icn_layer.pit.add_pit_entry(name, from_face_id_1, to_face_id, interest, False)
        self.assertEqual(self.icn_layer.pit.get_container_size(), 1)
        self.assertEqual(self.icn_layer.pit.find_pit_entry(name).name, name)

        # test retransmit 1
        self.icn_layer.ageing()
        time.sleep(0.1)
        self.assertFalse(self.icn_layer.queue_to_lower.empty())
        try:
            rface_id, rinterest = self.icn_layer.queue_to_lower.get(timeout=2.0)
        except:
            self.fail()
        self.assertEqual(self.icn_layer.pit.get_container_size(), 1)
        self.assertEqual(rface_id, to_face_id)
        self.assertEqual(rinterest, interest)

        # test retransmit 2
        self.icn_layer.ageing()
        time.sleep(0.1)
        self.assertFalse(self.icn_layer.queue_to_lower.empty())
        try:
            rface_id, rinterest = self.icn_layer.queue_to_lower.get(timeout=2.0)
        except:
            self.fail()
        self.assertEqual(self.icn_layer.pit.get_container_size(), 1)
        self.assertEqual(rface_id, to_face_id)
        self.assertEqual(rinterest, interest)

        # Wait for timeout
        time.sleep(2)

        # test retransmit 3 to get number of retransmit
        self.icn_layer.ageing()
        time.sleep(0.1)
        self.assertFalse(self.icn_layer.queue_to_lower.empty())
        try:
            rface_id, rinterest = self.icn_layer.queue_to_lower.get(timeout=2.0)
        except:
            self.fail()
        self.assertEqual(self.icn_layer.pit.get_container_size(), 1)
        self.assertEqual(rface_id, to_face_id)
        self.assertEqual(rinterest, interest)

        # test remove pit entry
        self.icn_layer.ageing()
        # nack = self.icn_layer.queue_to_lower.get(timeout=8.0) # invalid, no PIT Timeout Nack anymore
        # self.assertEqual(nack, [1, Nack(rinterest.name, NackReason.PIT_TIMEOUT, rinterest)])
        self.assertTrue(self.icn_layer.queue_to_lower.empty())
        self.assertEqual(self.icn_layer.pit.get_container_size(), 0)

    def test_ICNLayer_ageing_cs(self):
        """Test CS ageing and static entries"""

        self.icn_layer.start_process()
        name1 = Name("/test/data")
        content1 = Content(name1, "HelloWorld")

        name2 = Name("/data/test")
        content2 = Content(name2, "Goodbye")

        self.icn_layer.cs.add_content_object(content1)
        self.icn_layer.cs.add_content_object(content2, static=True)

        self.assertEqual(self.icn_layer.cs.get_container_size(), 2)
        self.assertEqual(self.icn_layer.cs.find_content_object(name1).content, content1)
        self.assertEqual(self.icn_layer.cs.find_content_object(name2).content, content2)

        #Test aging 1
        self.icn_layer.ageing()
        self.assertEqual(self.icn_layer.cs.get_container_size(), 2)
        self.assertEqual(self.icn_layer.cs.find_content_object(name1).content, content1)
        self.assertEqual(self.icn_layer.cs.find_content_object(name2).content, content2)

        time.sleep(2)
        # Test aging 2
        self.icn_layer.ageing()
        self.assertEqual(self.icn_layer.cs.get_container_size(), 1)
        self.assertEqual(self.icn_layer.cs.find_content_object(name2).content, content2)

    def test_ICNLayer_content_from_app_layer_no_pit(self):
        """get content from app layer when there is no pit entry available"""
        queue_to_higher = multiprocessing.Queue()
        queue_from_higher = multiprocessing.Queue()
        self.icn_layer.queue_to_higher = queue_to_higher
        self.icn_layer.queue_from_higher = queue_from_higher
        self.icn_layer.start_process()

        n = Name("/test/data")
        c = Content(n, "HelloWorld")
        self.icn_layer.queue_from_higher.put([0, c])
        time.sleep(1)
        self.assertTrue(self.queue1_icn_routing_down.empty())

    def test_ICNLayer_content_from_app_layer(self):
        """get content from app layer when there is a pit entry available"""
        queue_to_higher = multiprocessing.Queue()
        queue_from_higher = multiprocessing.Queue()
        self.icn_layer.queue_to_higher = queue_to_higher
        self.icn_layer.queue_from_higher = queue_from_higher
        self.icn_layer.start_process()
        face_id = 1
        n = Name("/test/data")
        self.icn_layer.pit.add_pit_entry(n, face_id, -1)
        self.assertEqual(self.icn_layer.pit.get_container_size(), 1)
        c = Content(n, "HelloWorld")
        self.icn_layer.queue_from_higher.put([0, c])
        try:
            data = self.icn_layer.queue_to_lower.get(timeout=2.0)
        except:
            self.fail()
        self.assertEqual(data, [face_id, c])

    def test_ICNLayer_content_to_app_layer_no_pit(self):
        """get content to app layer no pit"""
        queue_to_higher = multiprocessing.Queue()
        queue_from_higher = multiprocessing.Queue()
        self.icn_layer.queue_to_higher = queue_to_higher
        self.icn_layer.queue_from_higher = queue_from_higher
        self.icn_layer.start_process()
        from_face_id = 1
        n = Name("/test/data")
        c = Content(n, "HelloWorld")
        self.icn_layer.queue_from_lower.put([from_face_id, c])
        time.sleep(1)
        self.assertTrue(self.icn_layer.queue_to_higher.empty())
        
    def test_ICNLayer_content_to_app_layer(self):
        """get content to app layer"""
        queue_to_higher = multiprocessing.Queue()
        queue_from_higher = multiprocessing.Queue()
        self.icn_layer.queue_to_higher = queue_to_higher
        self.icn_layer.queue_from_higher = queue_from_higher
        self.icn_layer.start_process()
        face_id = -1
        from_face_id = 1
        n = Name("/test/data")
        self.icn_layer.pit.add_pit_entry(n, face_id, -1, interest=None, local_app=True)
        self.assertEqual(self.icn_layer.pit.get_container_size(), 1)
        c = Content(n, "HelloWorld")
        self.icn_layer.queue_from_lower.put([from_face_id, c])
        try:
            data = self.icn_layer.queue_to_higher.get(timeout=2.0)
        except:
            self.fail()
        self.assertEqual(data, [1, c])

    def test_ICNLayer_interest_from_app_layer_no_pit(self):
        """Test sending and interest message from APP with no PIT entry"""
        queue_to_higher = multiprocessing.Queue()
        queue_from_higher = multiprocessing.Queue()
        self.icn_layer.queue_to_higher = queue_to_higher
        self.icn_layer.queue_from_higher = queue_from_higher
        self.icn_layer._interest_to_app=True
        self.icn_layer.start_process()
        face_id = 1
        n = Name("/test/data")
        i = Interest(n)
        self.icn_layer.fib.add_fib_entry(n, [face_id], True)
        self.icn_layer.queue_from_higher.put([0, i])
        try:
            to_faceid, data = self.icn_layer.queue_to_lower.get(timeout=2.0)
        except:
            self.fail()
        self.assertEqual(to_faceid, face_id)
        self.assertEqual(i, data)
        self.assertEqual(self.icn_layer.pit.find_pit_entry(n).interest, i)
        self.assertTrue(self.icn_layer.pit.find_pit_entry(n).local_app[0])

    def test_ICNLayer_interest_from_app_layer_pit(self):
        """Test sending and interest message from APP with a PIT entry --> interest not for higher layer"""
        queue_to_higher = multiprocessing.Queue()
        queue_from_higher = multiprocessing.Queue()
        self.icn_layer.queue_to_higher = queue_to_higher
        self.icn_layer.queue_from_higher = queue_from_higher
        self.icn_layer._interest_to_app=True
        self.icn_layer.start_process()
        face_id = 1
        from_face_id = 2
        n = Name("/test/data")
        i = Interest(n)
        self.icn_layer.fib.add_fib_entry(n, [face_id], True)
        self.icn_layer.pit.add_pit_entry(n, from_face_id, face_id, i, local_app=False)
        self.assertFalse(self.icn_layer.pit.find_pit_entry(n).local_app[0])
        self.icn_layer.queue_from_higher.put([0, i])
        try:
            to_face_id, data = self.icn_layer.queue_to_lower.get(timeout=2.0)
        except:
            self.fail()
        self.assertEqual(to_face_id, face_id)
        self.assertEqual(i, data)
        self.assertEqual(self.icn_layer.pit.find_pit_entry(n).interest, i)
        self.assertFalse(self.icn_layer.pit.find_pit_entry(n).local_app[0]) #Just forward, not from local app

    def test_ICNLayer_interest_to_app_layer_no_pit(self):
        """Test sending and interest message from APP with no PIT entry"""
        queue_to_higher = multiprocessing.Queue()
        queue_from_higher = multiprocessing.Queue()
        self.icn_layer.queue_to_higher = queue_to_higher
        self.icn_layer.queue_from_higher = queue_from_higher
        self.icn_layer._interest_to_app = True
        self.icn_layer.start_process()
        face_id = 1
        from_face_id = 2
        n = Name("/test/data")
        i = Interest(n)
        self.icn_layer.fib.add_fib_entry(n, [face_id], True)
        self.icn_layer.queue_from_lower.put([from_face_id, i])
        try:
            data = self.icn_layer.queue_to_higher.get(timeout=2.0)
        except:
            self.fail()
        self.assertEqual(data[1], i)
        self.assertEqual(self.icn_layer.pit.find_pit_entry(n).interest, i)

    def test_ICNLayer_interest_to_app_layer_pit(self):
        """Test sending and interest message from APP with a PIT entry"""
        queue_to_higher = multiprocessing.Queue()
        queue_from_higher = multiprocessing.Queue()
        self.icn_layer.queue_to_higher = queue_to_higher
        self.icn_layer.queue_from_higher = queue_from_higher
        self.icn_layer._interest_to_app = True
        self.icn_layer.start_process()
        face_id = [1]
        from_face_id = 2
        n = Name("/test/data")
        i = Interest(n)
        self.icn_layer.fib.add_fib_entry(n, face_id, True)
        self.icn_layer.pit.add_pit_entry(n, from_face_id, face_id[0], i, local_app=False)
        self.icn_layer.queue_from_lower.put([from_face_id, i])
        time.sleep(1)
        self.assertTrue(self.icn_layer.queue_to_higher.empty()) #--> deduplication by pit entry

    def test_ICNLayer_interest_to_app_layer_cs(self):
        """Test sending and interest message from APP with a CS entry"""
        queue_to_higher = multiprocessing.Queue()
        queue_from_higher = multiprocessing.Queue()
        self.icn_layer.queue_to_higher = queue_to_higher
        self.icn_layer.queue_from_higher = queue_from_higher
        self.icn_layer._interest_to_app = True
        self.icn_layer.start_process()
        face_id = 1
        from_face_id = 2
        n = Name("/test/data")
        i = Interest(n)
        c = Content(n, "Hello World")
        self.icn_layer.fib.add_fib_entry(n, [face_id], True)
        self.icn_layer.cs.add_content_object(c)
        self.icn_layer.queue_from_lower.put([from_face_id, i])
        try:
            to_face_id, data = self.icn_layer.queue_to_lower.get(timeout=2.0)
        except:
            self.fail()
        self.assertEqual(to_face_id, from_face_id)
        self.assertEqual(data, c)
        self.assertTrue(self.icn_layer.queue_to_higher.empty())  # --> was answered by using Content from cache

    def test_ICNLayer_issue_nack_no_content_no_fib_from_lower(self):
        """Test if ICN Layer issues Nack if no content and no fib entry is available from lower"""
        self.icn_layer.start_process()
        interest = Interest("/test/data")
        nack = Nack(interest.name, NackReason.NO_ROUTE, interest=interest)
        self.icn_layer.queue_from_lower.put([1, interest])
        try:
            data = self.icn_layer.queue_to_lower.get(timeout=2.0)
        except:
            self.fail()
        fid = data[0]
        packet = data[1]
        self.assertEqual(fid, 1)
        self.assertEqual(packet, nack)

    def test_ICNLayer_issue_nack_no_content_no_fib_from_higher(self):
        """Test if ICN Layer issues Nack if no content and no fib entry is available from higher"""
        queue_to_higher = multiprocessing.Queue()
        queue_from_higher = multiprocessing.Queue()
        self.icn_layer.queue_to_higher = queue_to_higher
        self.icn_layer.queue_from_higher = queue_from_higher
        self.icn_layer.start_process()
        interest = Interest("/test/data")
        nack = Nack(interest.name, NackReason.NO_ROUTE, interest=interest)
        self.icn_layer.queue_from_higher.put([1, interest])
        try:
            data = self.icn_layer.queue_to_higher.get(timeout=2.0)
        except:
            self.fail()
        fid = data[0]
        packet = data[1]
        self.assertEqual(fid, 1)
        self.assertEqual(packet, nack)
    #TODO CHECK
    def test_ICNLayer_handling_nack_no_fib(self):
        """Test if ICN Layer handles a Nack correctly if no fib entry is available"""
        self.icn_layer.start_process()
        n1 = Name("/test/data")
        i1 = Interest(n1)
        fid_1 = 1
        nack_1 = Nack(n1, NackReason.NO_ROUTE, interest=i1)
        self.icn_layer.pit.add_pit_entry(n1, fid_1, -1, i1, False)
        self.icn_layer.queue_from_lower.put([2, nack_1])
        try:
            data = self.icn_layer.queue_to_lower.get(timeout=2.0)
            print(data)
        except:
            self.fail()
        self.assertEqual(data[0], fid_1)
        self.assertEqual(data[1], nack_1)

    #TODO Fix the error
    def test_ICNLayer_handling_nack_next_fib(self):
        """Test if ICN Layer handles a Nack correctly if further fib entry is available"""
        self.icn_layer.start_process()
        n1 = Name("/test/data/d1")
        i1 = Interest(n1)
        from_fid = 1
        to_fib1 = 2
        to_fib2 = 3
        to_fib3 = 4
        nack_1 = Nack(n1, NackReason.NO_ROUTE, interest=i1)

        self.icn_layer.pit.add_pit_entry(n1, from_fid, to_fib3, i1, None)
        self.icn_layer.pit.add_used_fib_face(n1, [to_fib3])

        self.icn_layer.fib.add_fib_entry(Name("/test"), [to_fib1])
        self.icn_layer.fib.add_fib_entry(Name("/test/data"), [to_fib2])
        self.icn_layer.fib.add_fib_entry(Name("/test/data/d1"), [to_fib3]) #assuming this entry was used first and is active when nack arrives
        self.icn_layer.queue_from_lower.put([to_fib3, nack_1])

        try:
            data = self.icn_layer.queue_to_lower.get(timeout=2.0)
        except:
             self.fail()

        self.assertEqual(data[0], to_fib2)
        self.assertEqual(data[1], i1)
        #check testing second path
        self.icn_layer.queue_from_lower.put([to_fib2, nack_1])
        try:
            data = self.icn_layer.queue_to_lower.get(timeout=2.0)

        except:
            self.fail()
        self.assertEqual(data[0], to_fib1)
        self.assertEqual(data[1], i1)
        #check no path left
        self.icn_layer.queue_from_lower.put([to_fib1, nack_1])
        try:
            data = self.icn_layer.queue_to_lower.get(timeout=2.0)
        except:
            self.fail()
        self.assertEqual(data[0], from_fid)
        self.assertEqual(data[1], nack_1)


    def test_multicast_and_nack_handling(self):
        """Test if a multicast works, and if the nack counter for the multicast works"""

        i1 = Interest("/test/data")
        n1 = Nack(i1.name, NackReason.NO_CONTENT, i1)

        self.icn_layer.start_process()

        self.icn_layer.fib.add_fib_entry(i1.name, [2,3,4])

        self.icn_layer.queue_from_lower.put([1, i1])

        d1 = self.icn_layer.queue_to_lower.get(timeout=2.0)
        self.assertEqual([2, i1], d1)

        self.assertTrue(self.icn_layer.queue_to_lower.empty())


        self.icn_layer.queue_from_lower.put([2, n1])
        d2 = self.icn_layer.queue_to_lower.get(timeout=4.0)
        print(d2)
        self.assertEqual([3, i1], d2)

        self.assertTrue(self.icn_layer.queue_to_lower.empty())

        self.icn_layer.queue_from_lower.put([3, n1])
        try:
            d3 = self.icn_layer.queue_to_lower.get(timeout=4.0)
        except:
            self.fail()
        print(d3)
        self.assertEqual([4, i1], d3)
        ##
        #
        #
        # self.assertTrue(self.icn_layer.queue_to_lower.empty())
        #
        # self.icn_layer.queue_from_lower.put([2, n1])
        # d3 = self.icn_layer.queue_to_lower.get(timeout=2.0)
        # self.assertEqual([1, n1], d3)

    def test_communicating_vessels_forwarding_strategy(self):
        """This function test the whole idea of forwarding strategy with multiple PIT entries
         and multiple FIB entries with multiple matches in PIT and FIB and also it checks the NACK handler in case of one face was nacked in a fib entry or all faces
          of a fib entry was nacked"""

        ab_name = Name("/a/b")
        i1 = Interest("/a/b/x")
        i2 = Interest("/a/b/y")
        i3 = Interest("/a/b/z")
        i4 = Interest("/a/b/w")
        i5 = Interest("/a/b/k")


        i6 = Interest("/x/y")
        i7 = Interest("/x")
        i8 = Interest("/m/n")
        i9 = Interest("/o/p")

        n1 = Nack(i1.name, NackReason.NO_CONTENT, i1)



        self.icn_layer.start_process()
        self.icn_layer.fib.add_fib_entry(ab_name, [1, 2, 3])
        # here the fib table has many entries which contains the prefix of ab_name
        self.icn_layer.fib.add_fib_entry(i6.name, [1, 4])
        self.icn_layer.fib.add_fib_entry(i7.name, [2, 3])
        self.icn_layer.fib.add_fib_entry(i8.name, [1, 5])
        self.icn_layer.fib.add_fib_entry(i9.name, [5, 3])

        #send the first interest ("/a/b/x") with no matching PIT entry. The outgoing face should be "1"
        #as it is the first Interest and there is no pending Interests to affect the decision
        self.icn_layer.queue_from_lower.put([10, i1])
        d1 = self.icn_layer.queue_to_lower.get(timeout=2.0)
        pit_entry = self.icn_layer.pit.find_pit_entry(i1.name)
        self.assertEqual([1], pit_entry.outgoing_faces)

        #send the second Interest ("/a/b/y") while the PIT entry of ("a/b/x") was not removed yet from the PIT
        #The interest should be sent to face "2" as the occupancy of face "1" is higher than the occupancy of "2" and "3"
        self.icn_layer.queue_from_lower.put([10, i2])
        d1 = self.icn_layer.queue_to_lower.get(timeout=2.0)
        pit_entry = self.icn_layer.pit.find_pit_entry(i2.name)
        self.assertEqual([2], pit_entry.outgoing_faces)

        #send bunch of Interests which are ("/x/y"), ("/x"), ("/m/n"),("/o/p"). In this case and because there is no matching entry in PIT for any of them.
        # each one will be sent to the first avaialble face in FIB. So i6 will be sent to 1. i7 will be sent to 2...

        self.icn_layer.queue_from_lower.put([10, i6])
        d1 = self.icn_layer.queue_to_lower.get(timeout=2.0)
        self.icn_layer.queue_from_lower.put([10, i7])
        d1 = self.icn_layer.queue_to_lower.get(timeout=2.0)
        self.icn_layer.queue_from_lower.put([10, i8])
        d1 = self.icn_layer.queue_to_lower.get(timeout=2.0)
        self.icn_layer.queue_from_lower.put([10, i9])
        d1 = self.icn_layer.queue_to_lower.get(timeout=2.0)

        # send the second Interest i3 ("/a/b/z") while the PIT entry of ("a/b/x") and ("a/b/y") was not removed yet from the PIT
        # The interest should be sent to face "3" as the occupancy of face "1" and face "2" is higher than the occupancy of "3"
        self.icn_layer.queue_from_lower.put([10, i3])
        d1 = self.icn_layer.queue_to_lower.get(timeout=2.0)
        pit_entry = self.icn_layer.pit.find_pit_entry(i3.name)
        self.assertEqual([3], pit_entry.outgoing_faces)


        # now send an interest i4 (("/a/b/w") while the previous three matching interests still exist in PIT. All faces have equal capacity so it will be sent to the first one.
        self.icn_layer.queue_from_lower.put([10, i4])
        d1 = self.icn_layer.queue_to_lower.get(timeout=2.0)
        pit_entry = self.icn_layer.pit.find_pit_entry(i4.name)
        self.assertEqual([1], pit_entry.outgoing_faces)

        # we are removing i4 and i1 from the PIT table
        self.icn_layer.pit.remove_pit_entry(i4.name)
        self.icn_layer.pit.remove_pit_entry(i1.name)

        # senf=d i5 while i2 and i3 still exist in PIT and they match i5. So the interest will be sent to face 1 because i2 is sent to 2 and i3 is sent to 3 so 2,3 have higher occupancy than 1
        self.icn_layer.queue_from_lower.put([10, i5])
        d1 = self.icn_layer.queue_to_lower.get(timeout=2.0)
        pit_entry = self.icn_layer.pit.find_pit_entry(i5.name)
        self.assertEqual([1], pit_entry.outgoing_faces)