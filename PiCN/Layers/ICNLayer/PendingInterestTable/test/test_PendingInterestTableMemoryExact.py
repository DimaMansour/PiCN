"""Tests for the in Memory Content Store with exact matching"""

import multiprocessing
import unittest

from PiCN.Layers.ICNLayer.PendingInterestTable.PendingInterestTableMemoryExact import PendingInterstTableMemoryExact
from PiCN.Layers.ICNLayer.ForwardingInformationBase import ForwardingInformationBaseEntry
from PiCN.Packets import Name


class test_PendingInterstTableMemoryExact(unittest.TestCase):
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.pit: PendingInterstTableMemoryExact = PendingInterstTableMemoryExact()

    def tearDown(self):
        pass

    def test_add_data_to_pit(self):
        """Test adding data to PIT"""
        fid = 1
        fake_outgoing_face = 15
        name = Name("/test/data")
        self.pit.add_pit_entry(name, fid, fake_outgoing_face)
        data = self.pit._container[0]
        self.assertEqual(data.name, name)

    def test_find_data_in_pit(self):
        """Test finding data in PIT exact"""
        fid = 1
        fake_outgoing_face = 15
        name = Name("/test/data")
        self.pit.add_pit_entry(name, fid, fake_outgoing_face)
        data = self.pit._container[0]
        self.assertEqual(data.name, name)
        res = self.pit.find_pit_entry(name)
        self.assertEqual(res.name, name)
        self.assertEqual(res.face_id, [fid])

    def test_find_data_in_pit_no_match(self):
        """Test finding data in PIT exact, with no match"""
        fid = 1
        fake_outgoing_face = 15
        name1 = Name("/test/data")
        name2 = Name("/data/test")
        self.pit.add_pit_entry(name1, fid, fake_outgoing_face)
        data = self.pit._container[0]
        self.assertEqual(data.name, name1)
        res = self.pit.find_pit_entry(name2)
        self.assertEqual(res, None)

    def test_find_data_to_pit_deduplication(self):
        """Test finding data in PIT with multiple fids"""
        fid1 = 1
        fid2 = 2
        outgoing_face = 15
        outgoing_face2 = 16
        name = Name("/test/data")
        self.pit.add_pit_entry(name, fid1, outgoing_face)
        self.pit.add_pit_entry(name, fid2, outgoing_face2)
        data = self.pit._container[0]
        self.assertEqual(data.name, name)
        res = self.pit.find_pit_entry(name)
        self.assertEqual(res.name, name)
        self.assertEqual(res.face_id, [fid1, fid2])
        self.assertEqual(res.outgoing_faces, [outgoing_face, outgoing_face2])

    def test_find_data_to_pit_deduplication_samefid(self):
        """Test finding data in PIT with two time same fids"""
        fid = 1
        outgoing_face = 15
        outgoing_face2 = 16
        name = Name("/test/data")
        self.pit.add_pit_entry(name, fid, outgoing_face)
        self.pit.add_pit_entry(name, fid, outgoing_face2)
        self.pit.add_pit_entry(name, fid, outgoing_face2)
        data = self.pit._container[0]
        self.assertEqual(data.name, name)
        res = self.pit.find_pit_entry(name)
        self.assertEqual(res.name, name)
        self.assertEqual(res.face_id, [fid])
        self.assertEqual(res.outgoing_faces, [outgoing_face, outgoing_face2])

    def test_remove_data_from_pit(self):
        """Test removing data from PIT"""
        fid = 1
        outgoing_face = 15
        name = Name("/test/data")
        self.pit.add_pit_entry(name, fid, outgoing_face)

        data = self.pit._container[0]
        self.assertEqual(data.name, name)
        self.assertEqual(len(self.pit._container), 1)
        self.pit.remove_pit_entry(name)
        self.assertEqual(len(self.pit._container), 0)

    #TODO: Check HERE
    def test_add_already_used_fib_face(self):
        """Test adding an already used FIB face"""
        n1 = Name("/test/data")
        fib_entry = ForwardingInformationBaseEntry(n1, 2, False)
        self.pit.add_pit_entry(n1, 1, 2, None, False)
        self.pit.add_used_fib_face(n1, fib_entry.faceid)
        self.assertEqual(self.pit.get_already_used_pit_entries(n1)[0], fib_entry.faceid )

    def test_set_number_of_forwards(self):
        """Test setting the number of forwards used in parallel, important for nack handling"""
        n1 = Name("/test/data")
        outgoing_face = 15
        self.pit.add_pit_entry(n1, [1], outgoing_face, None, False)
        self.pit.set_number_of_forwards(n1, 3)
        entry = self.pit.find_pit_entry(n1)

        self.assertEqual(entry.number_of_forwards, 3)

    def test_add_interested_face(self):
        """Test the addition of an interested face to an existing PIT entry"""
        fid = 1
        fid2 = 2
        outgoing_face = 15
        name = Name("/test/data")
        self.pit.add_pit_entry(name, fid, outgoing_face)
        self.pit.add_interested_face(name, fid2)
        pit_entry = self.pit.find_pit_entry(name)
        self.assertEqual(pit_entry.faceids, [fid, fid2])

    def test_occupancy_available_faces_per_name(self):
        name = Name("/a/b")
        fib_entry = ForwardingInformationBaseEntry(name, 1, False)
        fib_entry_faces = [1,2,3]
        fib_entry.faceid = fib_entry_faces

        pit_name1 = Name("/a/b")
        pit_name2 = Name("/x/y/z")
        pit_name3 = Name("/m/n")
        pit_name4 = Name("/a/b/c")
        pit_name5 = Name("/l/o")
        pit_name6 = Name("/a/b/c/d")

        self.pit.add_pit_entry(pit_name1, 7, 1, None, False)
        self.pit.add_pit_entry(pit_name2, 5, 1, None, False)
        self.pit.add_pit_entry(pit_name3, 6, 3, None, False)
        self.pit.add_pit_entry(pit_name4, 8, 1, None, False)
        self.pit.add_pit_entry(pit_name5, 9, 2, None, False)
        self.pit.add_pit_entry(pit_name6, 4, 2, None, False)

        result = self.pit.occupancy_available_faces_per_name(fib_entry)
        print(result[1])
        print(result[2])
        print(result[3])
        self.assertEqual(result[1], 2)
        self.assertEqual(result[2], 1)
        self.assertEqual(result[3], 0)
        self.assertEqual(len(result), 3)
