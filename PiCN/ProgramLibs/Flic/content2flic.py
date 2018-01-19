#!/usr/bin/env python3

# content2flic.py
#   implements the FLIC producer side

# (c) 2018-01-19 <christian.tschudin@unibas.ch>

class FLICer():

    def __init__(self, encoder, repo, MTU=4000):
        self.encoder = encoder
        self.repo = repo
        self.MTU = MTU
        pass

    def _mkChunk(self, dataL bytes):
        # input: bytes
        # output: (name, chunk)
        return None

    def bytesToManifest(self, data: bytes):
        # input: byte array
        # output: (nameOfRootManifest, rootManifestChunk)

        # cut content in pieces
        raw = []
        while len(data) > 0:
            raw.append(data[:MTU])
            data = data[MTU:]

        # persist pieces (and learn their names)
        names = []
        for r in raw:
            name, chunk = self._mkChunk(self.encoder, r)
            self.repo.write(name.as_string(), chunk)
            names.append(name.as_TLVbytes())

        # create list of index tables, the M pointers will be added later
        # -> DDDDDDM -> DDDDDM -> ...
        tables = []
        while len(names) > 0:
            tbl = '' # index table
            while len(names) > 0:
                n = names[0].as_bytes()
                # collect pointers as long as the manifest fits in a chunk
                if len(tbl) + len(n) + 100 > self.MTU:
                    break
                tbl += n
                names = names[1:]
            tables.append(tbl)

        # persist the manifests, start at the end, add the M pointers
        tailName =''
        while len(manifests) > 0:
            tbl = tables[-1]
            tbl += tailName
            # TODO: add TLV for index table, incl manifest TLV
            # tbl = ... (tbl)
            name, chunk = self._mkChunk(self.encoder, tbl)
            self.repo.write(name.as_string(), chunk)
            tailName = name.as_bytes()
            tables = tables[:-1]

        # chunk = ... (chunk)
        return (name.as_string(), chunk)

    def bytesToNFNresult(self, data: bytes, forceManifest=False):
        # input: e2e result bytes, as produced by NFN execution
        # output: "NFN result TLV", either constant or indirect (=manifest)

        if len(data) < self.MTU and not forceManifest:
            # TODO: add TLV for NFN direct result
            # data = ... (data)
            return data

        name, manifest = self.bytesToManifest(data)
    
        # TODO: add TLV for NFN indirect result
        # manifest = ... (manifest)
        return manifest

# eof
