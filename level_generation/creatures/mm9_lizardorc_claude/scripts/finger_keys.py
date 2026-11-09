#!/usr/bin/env python3
"""Hold the right fist in every clip: hand poses of work/hand_poses.json (fist.py): the finger bones of the right hand keep the grip, the hand's keys take the constant wrist turn, Bone07 stays where MM9 holds the cutlass. Args: <in glb> <out glb>"""
import json, sys
import numpy as np
from pygltflib import GLTF2
IN, OUT = sys.argv[1:3]
g = GLTF2().load(IN); P = json.load(open('work/hand_poses.json')); blob = bytearray(g.binary_blob())
def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
def rd(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()
def wr(i, arr):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; off = (bv.byteOffset or 0) + (a.byteOffset or 0); blob[off:off + arr.size * 4] = arr.astype('f4').tobytes()
done = 0
for an in g.animations:
    for ch in an.channels:
        n = g.nodes[ch.target.node].name; sm = an.samplers[ch.sampler]
        if ch.target.path == 'rotation':
            if n in P['hand_offset']:
                v = rd(sm.output); o = np.array(P['hand_offset'][n]); wr(sm.output, np.array([qmul(q, o) for q in v])); done += 1
            elif n in P['grip']:
                v = rd(sm.output); wr(sm.output, np.tile(np.array(P['grip'][n]), (len(v), 1))); done += 1
            elif n == 'Bone07':
                v = rd(sm.output); wr(sm.output, np.tile(np.array(P['weapon']['q']), (len(v), 1))); done += 1
        elif ch.target.path == 'translation' and n == 'Bone07':
            v = rd(sm.output); wr(sm.output, np.tile(np.array(P['weapon']['t']), (len(v), 1))); done += 1
for n, nd in ((x.name, x) for x in g.nodes):
    if n == 'Bone07': nd.rotation = P['weapon']['q']; nd.translation = P['weapon']['t']
    if n in P['grip']: nd.rotation = P['grip'][n]
g.set_binary_blob(bytes(blob)); g.save(OUT); print('FINGERS', done, 'channels')
