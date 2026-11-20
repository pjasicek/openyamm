#!/usr/bin/env python3
"""The floor pass raises a corpse per key, which shakes the whole body. The pelvis lift it added is dilated and low-passed (never lower than needed), so the fall stays one curve. Args: before.glb after.glb out.glb Clip..."""
import sys
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
from pygltflib import GLTF2, Accessor, BufferView
BE, AF, OUT = sys.argv[1:4]
gb = GLTF2().load(BE); ga = GLTF2().load(AF); bb = gb.binary_blob(); blob = bytearray(ga.binary_blob())
nb = [n.name for n in gb.nodes]; na = [n.name for n in ga.nodes]
def read(g, data, i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; o = (bv.byteOffset or 0) + (a.byteOffset or 0)
    return np.frombuffer(bytes(data[o:o + 12 * a.count]), 'f4').reshape(-1, 3).copy()
for clip in sys.argv[4:]:
    a1 = next(a for a in ga.animations if a.name == clip)
    c1 = next(c for c in a1.channels if na[c.target.node] == 'Scene Root' and c.target.path == 'translation')
    v1 = read(ga, blob, a1.samplers[c1.sampler].output)
    d = v1[:, 1].copy()
    if clip in ('Walking', 'Backpedal', 'BackpedalRun'):       # a loop: a plain cyclic low-pass
        e = gaussian_filter1d(d, 2.2, mode='wrap')
    else:
        e = gaussian_filter1d(maximum_filter1d(d, 7, mode='nearest'), 2.5, mode='nearest')
        e = np.maximum(e, gaussian_filter1d(d, 1.0, mode='nearest'))
        e = gaussian_filter1d(e, 1.2, mode='nearest')
        e[-1] = d[-1]; e[-2] = 0.5 * (d[-1] + e[-3])
    v1[:, 1] = e
    while len(blob) % 4: blob.append(0)
    o = len(blob); da = v1.astype('f4').tobytes(); blob += da
    ga.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(da)))
    ga.accessors.append(Accessor(bufferView=len(ga.bufferViews) - 1, componentType=5126, count=len(v1), type='VEC3', min=v1.min(0).tolist(), max=v1.max(0).tolist()))
    a1.samplers[c1.sampler].output = len(ga.accessors) - 1
    print('LIFT smooth', clip, round(float(d.max()), 3), round(float(np.abs(np.diff(d, 2)).max() * 1000), 1), '->', round(float(np.abs(np.diff(e, 2)).max() * 1000), 1), 'mm/f2')
ga.buffers[0].byteLength = len(blob); ga.set_binary_blob(bytes(blob)); ga.save(OUT)
