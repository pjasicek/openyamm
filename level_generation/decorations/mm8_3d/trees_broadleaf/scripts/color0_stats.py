#!/usr/bin/env python3
"""COLOR_0 luminance percentiles (linear, Rec. 709 weights; p5 / p50 / p95) per material of a tree GLB's LOD0 and LOD1
meshes, for the Shell and Leaves materials (and Moss when present). Usage: color0_stats.py <glb> [tag]"""
import json, os, sys
from pathlib import Path
import numpy as np
REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link

doc, binary = link.read_glb(Path(sys.argv[1]))


def accessor(index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    x = np.frombuffer(bytes(binary[off:off + a['count'] * n * np.dtype(dt).itemsize]), dt).reshape(a['count'], n)
    x = x.astype(np.float64)
    if a['componentType'] != 5126:
        x /= {5121: 255.0, 5123: 65535.0}[a['componentType']]
    return x


base = next(n for n in doc['nodes'] if 'mesh' in n)
chain = [base['mesh']] + doc['meshes'][base['mesh']]['extras']['openyamm_lods']
out = {}
for level, mi in zip(('LOD0', 'LOD1'), chain[:2]):
    for p in doc['meshes'][mi]['primitives']:
        name = doc['materials'][p['material']]['name']
        if name not in ('Shell', 'Leaves', 'Moss'):
            continue
        c = accessor(p['attributes']['COLOR_0'])[:, :3]
        lum = c @ [0.2126, 0.7152, 0.0722]
        out[f'{level} {name}'] = [round(float(v), 3) for v in np.percentile(lum, [5, 50, 95])]
print(json.dumps(out))
