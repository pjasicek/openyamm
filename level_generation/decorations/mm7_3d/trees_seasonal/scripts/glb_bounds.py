#!/usr/bin/env python3
"""LOD0 bounds (glTF, y up) of GLBs: glb_bounds.py a.glb [...]; with --json <id>, rewrites work/<id>/model.json from
work/reduce/mm7_deco_<id>.glb (the reduced model: LOD triangles, bounds, size)."""
import json, os, sys
from pathlib import Path
import numpy as np
import common
sys.path.insert(0, os.path.join(common.REPO, 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402


def info(path):
    doc, binary = read_glb(Path(path))
    node = next(n for n in doc['nodes'] if 'mesh' in n); mesh = doc['meshes'][node['mesh']]
    pts = np.concatenate([np.frombuffer(accessor_bytes(doc, binary, p['attributes']['POSITION']), np.float32).reshape(-1, 3)
                          for p in mesh['primitives']])
    # only vertices that triangles use (thinned cards leave unused vertices until compaction)
    used = []
    for p in mesh['primitives']:
        a = doc['accessors'][p['indices']]
        dt = {5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
        used.append(np.frombuffer(accessor_bytes(doc, binary, p['indices']), dt))
    chain = [node['mesh']] + mesh.get('extras', {}).get('openyamm_lods', [])
    tris = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][i]['primitives']) for i in chain]
    pos = []
    for p, u in zip(mesh['primitives'], used):
        v = np.frombuffer(accessor_bytes(doc, binary, p['attributes']['POSITION']), np.float32).reshape(-1, 3)
        pos.append(v[np.unique(u)])
    pos = np.concatenate(pos)
    return {'lod_triangles': tris, 'bounds_min': pos.min(0).tolist(), 'bounds_max': pos.max(0).tolist(),
            'file_bytes': os.path.getsize(path)}


if __name__ == '__main__' and sys.argv[1] == '--json':
    for sid in sys.argv[2:]:
        spec = common.load(sid)
        m = info(os.path.join(common.TREES, 'work', 'reduce', spec['output']))
        json.dump(m, open(os.path.join(spec['work'], 'model.json'), 'w'), indent=1)
        print('MODEL', sid, m['lod_triangles'], round(m['bounds_min'][1], 4), round(m['bounds_max'][1], 4))
elif __name__ == '__main__':
    for p in sys.argv[1:]:
        m = info(p); print(os.path.basename(p), m['lod_triangles'], 'y', round(m['bounds_min'][1], 4), round(m['bounds_max'][1], 4))
