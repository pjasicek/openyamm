#!/usr/bin/env python3
"""Right fist round the staff, solved on the hand's skin by grip_solve.py (2026-11-01: palm on the shaft, each phalanx curled until its skin
meets the shaft surface, thumb closing from the other side; r1-r13 solved finger joint points only and left the staff beside the fingertips).
The local rotations are written as constant keys of the R finger bones in EVERY clip (MM9 has one mitten finger joint there; the staff is
rigid to R Hand, so the fist stays closed). Args: <in glb> <out glb> <rig json> [report json]"""
import sys, json
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, matrix_quaternion
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget
IN, OUT, RIG = sys.argv[1:4]
from glb_pose import Model
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from grip_solve import solve, hand_data, g
R = json.load(open(RIG)); GR = R['grip']; F = R['fingers']
m = Model(Glb(IN)); Wb, verts = hand_data(m)
G, A = g(GR['point']), g(GR['axis']); A /= np.linalg.norm(A); n_palm = g(GR['palm_side']); n_palm /= np.linalg.norm(n_palm)
W, rep, _ = solve(Wb, verts, G, A, n_palm, {f: g(F[f][3]) for f in F})
local = {}
for f in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb'):
    bones = [f'Bip01 R {f}{k}' for k in (1, 2, 3)]; par = ['Bip01 R Hand'] + bones[:2]
    for b, p_ in zip(bones, par):
        L = np.linalg.inv(W[p_]) @ W[b]; local[b] = matrix_quaternion(L[:3, :3])
    print('GRIP', f, rep[f]['curl_deg'], 'pad gap cm', rep[f]['pad_gap_cm'])
print('GRIP palm gap cm', rep['palm_gap_cm'], 'inside cm', rep['inside_cm'])
g_ = GLTF2().load(IN); blob = bytearray(g_.binary_blob()); names = [n.name for n in g_.nodes]
def add(arr, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = np.ascontiguousarray(arr, 'f4').tobytes(); blob += d
    g_.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g_.accessors.append(Accessor(bufferView=len(g_.bufferViews) - 1, componentType=5126, count=len(arr), type=typ))
    return len(g_.accessors) - 1
for an in g_.animations:
    tin = an.samplers[an.channels[0].sampler].input; n = g_.accessors[tin].count
    an.channels = [c for c in an.channels if not (names[c.target.node] in local and c.target.path == 'rotation')]
    for b, q in local.items():
        s = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(np.repeat(np.asarray(q)[None], n, 0), 'VEC4'), interpolation='LINEAR'))
        an.channels.append(AnimationChannel(sampler=s, target=AnimationChannelTarget(node=names.index(b), path='rotation')))
g_.buffers[0].byteLength = len(blob); g_.set_binary_blob(bytes(blob)); g_.save(OUT)
if len(sys.argv) > 4: json.dump(rep, open(sys.argv[4], 'w'), indent=1)
