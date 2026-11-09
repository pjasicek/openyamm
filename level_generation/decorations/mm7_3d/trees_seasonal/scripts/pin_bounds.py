#!/usr/bin/env python3
"""Keep a reduced model's LOD0 height: the bark collapse (deco_ladder.py) can lift the lowest root tip by a few
millimetres, which would break the family rule (every season shares its LOD0 bounds height). The lowest bark vertex
of the reduced LOD0 goes back to the original LOD0 bottom (a root tip a few mm under the ground); the top comes from
leaf cards, which the collapse does not touch (checked). Then work/<id>/model.json is rewritten from the reduced file.
Usage: pin_bounds.py <id> [...]   (original work/<id>/mm7_deco_<id>.glb, reduced work/reduce/mm7_deco_<id>.glb)"""
import json, os, sys
from pathlib import Path
import numpy as np
import common
import glb_bounds
sys.path.insert(0, os.path.join(common.REPO, 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

for sid in sys.argv[1:]:
    spec = common.load(sid)
    original = glb_bounds.info(os.path.join(spec['work'], spec['output']))
    path = Path(common.TREES) / 'work' / 'reduce' / spec['output']
    doc, binary = read_glb(path); binary = bytearray(binary)
    node = next(n for n in doc['nodes'] if 'mesh' in n)
    prim = next(p for p in doc['meshes'][node['mesh']]['primitives'] if doc['materials'][p['material']]['name'] == 'Bark')
    acc = doc['accessors'][prim['attributes']['POSITION']]; view = doc['bufferViews'][acc['bufferView']]
    start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    pos = np.frombuffer(bytes(binary[start:start + acc['count'] * 12]), np.float32).reshape(-1, 3).copy()
    target = original['bounds_min'][1]
    k = int(pos[:, 1].argmin())
    moved = float(target - pos[k, 1])
    if abs(moved) > 1e-5:
        pos[k, 1] = target
        binary[start:start + acc['count'] * 12] = pos.tobytes()
        acc['min'] = pos.min(0).tolist(); acc['max'] = pos.max(0).tolist()
        write_glb(path, doc, bytes(binary))
    m = glb_bounds.info(str(path))
    assert abs(m['bounds_max'][1] - original['bounds_max'][1]) < 1e-4, ('top moved', m['bounds_max'][1], original['bounds_max'][1])
    assert abs(m['bounds_min'][1] - target) < 1e-5
    json.dump(m, open(os.path.join(spec['work'], 'model.json'), 'w'), indent=1)
    print('PINNED', sid, f'bottom moved {moved * 1000:.1f} mm', 'LOD', m['lod_triangles'],
          'y', round(m['bounds_min'][1], 4), round(m['bounds_max'][1], 4))
