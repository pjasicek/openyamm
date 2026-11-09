#!/usr/bin/env python3
"""MM9's club pivots inside a mitten fist (up to 109 deg against the hand). A real fist holds it, so the rotation goes to the wrist: LH' = LH * LY * LY0^-1 * C, with C = H0^-1 RD^-1 H0 the constant turn that lines the fist's hole up with MM9's axis; Yclub then stays at our rest, rigid in the fist, and the club keeps MM9's world direction in every frame. Solved on the same resampled curves, nothing per frame added. Args: <in glb> <out glb> <grip json>"""
import json, sys
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView
from scipy.spatial.transform import Rotation as Rt
IN, OUT, GR = sys.argv[1:4]
g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); gr = json.load(open(GR))
idx = {n.name: i for i, n in enumerate(g.nodes)}
hi, yi = idx['Bip01 R Hand'], idx['Yclub']
src = GLTF2().load('source/true/trellborg1_true.glb')
qY0 = Rt.from_quat(src.nodes[[n.name for n in src.nodes].index('Yclub')].rotation)
# gltf axes: Blender (x, y, z) = gltf (x, -z, y)
T = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)      # blender -> gltf
RD_g = T @ np.array(gr['RD']) @ T.T; H0_g = None
def world_rest(n):
    par = {c: i for i, x in enumerate(g.nodes) for c in (x.children or [])}
    R = Rt.identity()
    while True:
        x = g.nodes[n]; R = Rt.from_quat(x.rotation or [0, 0, 0, 1]) * R
        if n not in par: return R
        n = par[n]
H0 = world_rest(hi)
C = H0.inv() * Rt.from_matrix(RD_g).inv() * H0
def rd(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()
def wr(i, arr):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; o = (bv.byteOffset or 0) + (a.byteOffset or 0)
    blob[o:o + arr.size * 4] = arr.astype('f4').tobytes()
Yrest = np.array(g.nodes[yi].rotation or [0, 0, 0, 1]); Trest = np.array(g.nodes[yi].translation or [0, 0, 0])
mx = {}
for an in g.animations:
    ch = {(c.target.node, c.target.path): an.samplers[c.sampler] for c in an.channels}
    if (hi, 'rotation') not in ch or (yi, 'rotation') not in ch: print('SKIP', an.name); continue
    h, y = ch[(hi, 'rotation')], ch[(yi, 'rotation')]
    qh = rd(h.output); qy = rd(y.output)
    th, ty = rd(h.input)[:, 0], rd(y.input)[:, 0]
    if len(qy) != len(qh):
        qy = np.array([qy[int(np.argmin(np.abs(ty - t)))] for t in th])
    new = (Rt.from_quat(qh) * Rt.from_quat(qy) * qY0.inv() * C).as_quat()
    for k in range(1, len(new)):
        if new[k] @ new[k - 1] < 0: new[k] = -new[k]
    wr(h.output, new)
    wr(y.output, np.repeat(Yrest[None], g.accessors[y.output].count, 0))
    if (yi, 'translation') in ch:
        s = ch[(yi, 'translation')]; wr(s.output, np.repeat(Trest[None], g.accessors[s.output].count, 0))
    mx[an.name] = round(float(np.degrees((Rt.from_quat(new) * Rt.from_quat(g.nodes[hi].rotation or [0, 0, 0, 1]).inv()).magnitude()).max()), 0)
g.set_binary_blob(bytes(blob)); g.save(OUT)
print('CLUBKEYS', mx)
