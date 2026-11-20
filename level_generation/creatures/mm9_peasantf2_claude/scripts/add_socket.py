#!/usr/bin/env python3
"""Add an empty node at a rest position under a joint (an event socket). Usage: add_socket.py in.glb out.glb <name> <parent joint> <x y z glTF world>"""
import json, struct, sys
import numpy as np
src, dst, name, parent = sys.argv[1:5]
P = np.array([float(x) for x in sys.argv[5:8]])
raw = open(src, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); blob = raw[20 + n + 8:]
par = {}
for i, nd in enumerate(doc['nodes']):
    for c in nd.get('children', []): par[c] = i
def local(nd):
    T = np.eye(4); T[:3, 3] = nd.get('translation', [0, 0, 0])
    x, y, z, w = nd.get('rotation', [0, 0, 0, 1])
    T[:3, :3] = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    return T
names = {nd.get('name'): i for i, nd in enumerate(doc['nodes'])}
i = names[parent]; M = local(doc['nodes'][i]); j = i
while j in par:
    j = par[j]; M = local(doc['nodes'][j]) @ M
loc = np.linalg.inv(M) @ np.r_[P, 1]
doc['nodes'].append({'name': name, 'translation': [float(x) for x in loc[:3]]})
doc['nodes'][i].setdefault('children', []).append(len(doc['nodes']) - 1)
enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
open(dst, 'wb').write(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(blob)) + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(blob), 0x004e4942) + blob)
print('SOCKET', name, parent, loc[:3].round(3))
