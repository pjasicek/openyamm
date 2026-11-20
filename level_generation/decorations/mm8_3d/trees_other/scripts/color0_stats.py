#!/usr/bin/env python3
"""COLOR_0 linear luminance percentiles (p5 / p50 / p95) per material of a GLB's LOD0 mesh.
Usage: color0_stats.py <model.glb>..."""
import sys
import numpy as np
from overdraw import read_glb, accessor, lod_meshes
for path in sys.argv[1:]:
    doc, binary = read_glb(path)
    mesh = doc['meshes'][lod_meshes(doc)[0]]
    out = []
    for p in mesh['primitives']:
        name = doc['materials'][p['material']]['name']
        c = accessor(doc, binary, p['attributes']['COLOR_0']).astype(np.float64)[:, :3]
        lum = c @ np.array([0.2126, 0.7152, 0.0722])
        out.append(f"{name} {np.percentile(lum, 5):.3f}/{np.percentile(lum, 50):.3f}/{np.percentile(lum, 95):.3f}")
    print(path.split('/')[-1].replace('mm8_deco_', '').replace('.glb', ''), ' | '.join(out))
