#!/usr/bin/env python3
"""Leaking-shadow check in world units: for each shadow level s and each colour level c <= s (the shadow level is
usually equal to or coarser than the colour level, LOD_PLAYBOOK.md section 1), the share of the shadow mesh's surface
(6,000 area-weighted samples, bind pose) lying more than 1 and 2 world units outside colour level c, and the 99th
percentile. World units = metres x the binding's scale (the largest tier scale in actors.yml).
Usage: shadow_check.py <scale> <glb> -> one JSON line"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lod_static import Model, signed_outside, surface_samples  # noqa: E402


def merged(model, mesh_index):
    parts = [model.prim(p) for p in model.doc['meshes'][mesh_index]['primitives']]
    offsets = np.cumsum([0] + [len(x[0]) for x in parts])
    return (np.concatenate([x[0] for x in parts]),
            np.concatenate([x[1] + o for x, o in zip(parts, offsets)]))


def main():
    scale, path = float(sys.argv[1]), sys.argv[2]
    model = Model(path)
    doc = model.doc
    tri = lambda mi: sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][mi]['primitives'])
    nodes = [n for n in doc['nodes'] if 'mesh' in n and 'skin' in n
             and (doc['meshes'][n['mesh']].get('extras') or {}).get('openyamm_lods')]
    node = max(nodes, key=lambda n: tri(n['mesh']))
    extras = doc['meshes'][node['mesh']]['extras']
    colour = [merged(model, mi) for mi in [node['mesh']] + extras['openyamm_lods']]
    rng = np.random.default_rng(1)
    out = {'stem': Path(path).stem, 'scale': scale, 'pairs': {}}
    for s, mi in enumerate(extras.get('openyamm_shadow_lods', [])):
        points = surface_samples(*merged(model, mi), 6000, rng)
        for c in range(min(s, len(colour) - 1) + 1):
            d = signed_outside(points, *colour[c]) * scale
            out['pairs'][f's{s}c{c}'] = {'out1u': round(float((d > 1).mean()), 4),
                                         'out2u': round(float((d > 2).mean()), 4),
                                         'p99u': round(float(np.percentile(d, 99)), 2)}
    print(json.dumps(out), flush=True)


if __name__ == '__main__':
    main()
