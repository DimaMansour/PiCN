"""in-memory Pending Interest Table using exact prefix matching"""

import time

from typing import List
from PiCN.Layers.ICNLayer.PendingInterestTable.BasePendingInterestTable import BasePendingInterestTable, \
    PendingInterestTableEntry
from PiCN.Layers.ICNLayer.ForwardingInformationBase import ForwardingInformationBaseEntry
from PiCN.Packets import Interest, Name
from typing import List, Dict


class PendingInterstTableMemoryExact(BasePendingInterestTable):
    """in-memory Pending Interest Table using exact prefix matching"""

    def __init__(self, pit_timeout: int=4, pit_retransmits:int=3) -> None:
        super().__init__(pit_timeout=pit_timeout, pit_retransmits=pit_retransmits)

    def add_interested_face(self, name, face:int):
        for pit_entry in self.container:
            if pit_entry.name == name:
                if face in pit_entry.face_id:
                    return
                else:
                    self.container.remove(pit_entry)
                    pit_entry._faceids.append(face)
                    self.container.append(pit_entry)
                    return
            return

    def add_outgoing_face(self, name, face: int):
        for pit_entry in self.container:
            if pit_entry.name == name:
                if face in pit_entry.outgoing_faces:
                    return
                else:
                    self.container.remove(pit_entry)
                    pit_entry.outgoing_faces.append(face)
                    self.container.append(pit_entry)
                    return
            return

    def add_pit_entry(self, name, faceid: int, outgoing_face: int, interest: Interest = None, local_app = False):
        for pit_entry in self.container:
            if pit_entry.name == name:
                if faceid in pit_entry.face_id and local_app in pit_entry.local_app:
                    if outgoing_face in pit_entry.outgoing_faces:
                        return
                    else:
                        self.container.remove(pit_entry)
                        pit_entry.outgoing_faces.append(outgoing_face)
                        self.container.append(pit_entry)
                        return

                self.container.remove(pit_entry)
                pit_entry._faceids.append(faceid)
                pit_entry._local_app.append(local_app)
                if outgoing_face not in pit_entry.outgoing_faces:
                    pit_entry.outgoing_faces.append(outgoing_face)
                self.container.append(pit_entry)
                return
        self.container.append(PendingInterestTableEntry(name, faceid, outgoing_face, interest, local_app))
        # TODO check if this is a good idea to add the used face immediately on creation
        # self.add_used_fib_face(name, [outgoing_face])

    # this function returns a dict of fib available faces per name and the occupation of each one collected from PIT
    def occupancy_available_faces_per_name(self, fib_entry: ForwardingInformationBaseEntry) -> Dict:
        dict_of_faces_with_occupancy ={}
        fib_components = fib_entry.name.string_components
        for fib_face in fib_entry.faceid:
            number_of_appearance_in_pit = 0
            for pit_entry in self.container:
                if fib_face not in pit_entry.outgoing_faces:
                    continue

                pit_name_components = pit_entry.name.string_components
                full_match = True
                for i in range(0, len(fib_components))  :
                    if fib_components[i] != pit_name_components[i]:
                        full_match = False
                        break

                if full_match:
                    number_of_appearance_in_pit += 1

            dict_of_faces_with_occupancy[fib_face] = number_of_appearance_in_pit

        return dict_of_faces_with_occupancy


    def remove_pit_entry(self, name: Name):
        to_remove =[]
        for pit_entry in self.container:
            if(pit_entry.name == name):
                to_remove.append(pit_entry)
        for r in to_remove:
            self.container.remove(r)

    def find_pit_entry(self, name: Name) -> PendingInterestTableEntry:
        for pit_entry in self.container:
            if (pit_entry.name == name):
                return pit_entry
        return None

    def update_timestamp(self, pit_entry: PendingInterestTableEntry):
        self.container.remove(pit_entry)
        new_entry = PendingInterestTableEntry(pit_entry.name,
                                              pit_entry.faceids,
                                              outgoing_faces=pit_entry.outgoing_faces,
                                              interest=pit_entry.interest,
                                              local_app=pit_entry.local_app,
                                              fib_faces_already_used=pit_entry.fib_faces_already_used,
                                              faces_already_nacked=pit_entry.faces_already_nacked,
                                              number_of_forwards=pit_entry.number_of_forwards)
        new_entry.faces_already_nacked = pit_entry.faces_already_nacked
        self.container.append(new_entry)

    #TODO this should be changed to add_used_face_id
    def add_used_fib_face(self, name: Name, used_fib_face: List[int]):
        pit_entry = self.find_pit_entry(name)
        self.container.remove(pit_entry)
        pit_entry.fib_faces_already_used.extend(used_fib_face)
        self.container.append(pit_entry)

    def get_already_used_pit_entries(self, name: Name):
        pit_entry = self.find_pit_entry(name)
        return pit_entry.fib_faces_already_used

    def append(self, entry):
        self.container.append(entry)

    def ageing(self) -> List[PendingInterestTableEntry]:
        cur_time = time.time()
        remove = []
        updated = []
        for pit_entry in self.container:
            if pit_entry.timestamp + self._pit_timeout < cur_time and pit_entry.retransmits > self._pit_retransmits:
                remove.append(pit_entry)
            else:
                pit_entry.retransmits = pit_entry.retransmits + 1
                updated.append(pit_entry)
        for pit_entry in remove:
            self.remove_pit_entry(pit_entry.name)
        for pit_entry in updated:
            self.remove_pit_entry(pit_entry.name)
            self.container.append(pit_entry)
        return updated, remove
