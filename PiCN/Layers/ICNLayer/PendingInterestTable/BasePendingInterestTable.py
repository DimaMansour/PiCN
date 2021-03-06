"""Abstract BasePendingInterestTable for usage in BasicICNLayer"""

import abc
import multiprocessing
import time
from typing import List, Dict

from PiCN.Packets import Interest, Name
from PiCN.Layers.ICNLayer.ForwardingInformationBase import ForwardingInformationBaseEntry
from PiCN.Layers.ICNLayer import BaseICNDataStruct


class PendingInterestTableEntry(object):
    """An entry in the Forwarding Information Base"""

    def __init__(self, name: Name, faceid: int, outgoing_faces, interest:Interest = None, local_app: bool=False,
                 fib_faces_already_used: List[int]=None, faces_already_nacked=None,
                 number_of_forwards=0):
        self.name = name
        self._faceids: List[int] = []
        if isinstance(faceid, list):
            self._faceids.extend(faceid)
        else:
            self._faceids.append(faceid)

        self.outgoing_faces: List[int] = []
        if isinstance(outgoing_faces, list):
            self.outgoing_faces.extend(outgoing_faces)
        else:
            self.outgoing_faces.append(outgoing_faces)

        self._timestamp = time.time()
        self._retransmits = 0
        self._local_app: List[bool]= []
        if isinstance(local_app, list):
            self._local_app.extend(local_app)
        else:
            self._local_app.append(local_app)
        self._interest = interest
        if fib_faces_already_used: #default parameter is not [] but None and this if else is here because [] as default parameter leads to a strange behavior
            self._fib_faces_already_used: List[int] = fib_faces_already_used
        else:
            self._fib_faces_already_used: List[int] = []
        if faces_already_nacked:
            self.faces_already_nacked = faces_already_nacked
        else:
            self.faces_already_nacked = []
        self.number_of_forwards = number_of_forwards


    def __eq__(self, other):
        if other is None:
            return False
        return self.name == other.name

    @property
    def interest(self):
        return self._interest

    @interest.setter
    def interest(self, interest):
        self._interest = interest

    @property
    def faceids(self):
        return self._faceids

    @faceids.setter
    def face_id(self, faceids):
        self._faceids = faceids

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        self._timestamp

    @property
    def retransmits(self):
        return self._retransmits

    @retransmits.setter
    def retransmits(self, retransmits):
        self._retransmits = retransmits

    @property
    def local_app(self):
        return self._local_app

    @local_app.setter
    def local_app(self, local_app):
        self._local_app = local_app

    @property
    def interest(self):
        return self._interest

    @interest.setter
    def interest(self, interest):
        self._interest = interest

    @property
    def fib_faces_already_used(self):
        return self._fib_faces_already_used

    @fib_faces_already_used.setter
    def fib_faces_already_used(self, fib_faces_already_used):
        self._fib_faces_already_used = fib_faces_already_used


class BasePendingInterestTable(BaseICNDataStruct):
    """Abstract BasePendingInterestaTable for usage in BasicICNLayer
    :param pit_timeout: timeout for a pit entry when calling the ageing function
    """

    def __init__(self, pit_timeout: int=10, pit_retransmits: int=3):
        super().__init__()
        self.container: List[PendingInterestTableEntry] = []
        self._pit_timeout = pit_timeout
        self._pit_retransmits = pit_retransmits

    @abc.abstractmethod
    def add_pit_entry(self, name: Name, faceid: int, outgoing_face: int, interest: Interest = None, local_app: bool = False):
        """Add an new entry"""

    @abc.abstractmethod
    def add_interested_face(self, name, face: int):
        """update an existing entry by appending
         the interested face to the faceids. If there is not entry, nothing happens."""

    @abc.abstractmethod
    def add_outgoing_face(self, name, face: int):
        """This method an existing entry by appending
         the face to the outgoing_faces. If there is not entry, nothing happens."""
    @abc.abstractmethod
    def find_pit_entry(self, name: Name) -> PendingInterestTableEntry:
        """Find an entry in the PIT"""

    @abc.abstractmethod
    def remove_pit_entry(self, name: Name):
        """Remove an entry in the PIT"""

    @abc.abstractmethod
    def update_timestamp(self, pit_entry: PendingInterestTableEntry):
        """Update Timestamp of a PIT Entry"""

    @abc.abstractmethod
    def add_used_fib_face(self, name: Name, used_fib_face: List[int]):
        """Add a used fib entry to the already used fib faces"""

    @abc.abstractmethod
    def ageing(self) -> (List[PendingInterestTableEntry], List[PendingInterestTableEntry]):
        """Update the entries periodically
        :return List of PIT entries to be retransmitted and a list of the removed entries
        """

    @abc.abstractmethod
    def append(self, entry):
        """append an pit_entry to the pit container
        :param entry: entry to be appended
        """

    @abc.abstractmethod
    def get_already_used_pit_entries(self, name: Name):
        """Get already used fib entries"""


    #@abc.abstractmethod
    def occupancy_available_faces_per_name(self, fib_entry: ForwardingInformationBaseEntry) -> Dict:
        """This function takes a fib entry which matches the name with the availables faces
    and return the occupancy of each face organized in a dictionary (it returns a dictionary of faces and its occupation"""


    def set_number_of_forwards(self, name, forwards):
        pit_entry = self.find_pit_entry(name)
        if pit_entry:
            self.remove_pit_entry(name)
            pit_entry.number_of_forwards = forwards
            self.append(pit_entry)

    def increase_number_of_forwards(self, name):
        pit_entry = self.find_pit_entry(name)
        if pit_entry:
            self.remove_pit_entry(name)
            pit_entry.number_of_forwards = pit_entry.number_of_forwards + 1
            self.append(pit_entry)

    def decrease_number_of_forwards(self, name):
        pit_entry = self.find_pit_entry(name)
        if pit_entry:
            self.remove_pit_entry(name)
            pit_entry.number_of_forwards = pit_entry.number_of_forwards - 1
            self.append(pit_entry)

    def add_nacked_faceid(self, name, fid: int):
        pit_entry = self.find_pit_entry(name)
        if pit_entry:
            self.remove_pit_entry(name)
            pit_entry.faces_already_nacked.append(fid)
            self.append(pit_entry)

    def test_faceid_was_nacked(self, name, fid: int):
        pit_entry = self.find_pit_entry(name)
        if pit_entry:
            return (fid in pit_entry.faces_already_nacked)
        return False

    def set_pit_timeout(self, timeout: float):
        """set the timeout intervall for a pit entry
        :param timeout: timout value to be set
        """
        self._pit_timeout = timeout

    def set_pit_retransmits(self, retransmits: int):
        """set the max number of retransmits for a pit entry
        :param retransmits: retransmit value to be set
        """
        self._pit_retransmits = retransmits




