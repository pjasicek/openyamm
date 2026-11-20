#!/usr/bin/env python3
"""Shadow LOD1-3 pulled inside the LOD0 surface, as the m532 build does (mm8_m532_claude/scripts/postprocess_runtime.py:
push along the nearest LOD0 normal by the vertex's height above it plus 2 / 4 / 7 mm, capped at 15 mm).
Usage: shrink_shadow_lods.py <in.glb> <out.glb>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
repo = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(repo / 'tools'))
from merge_head_material import read_glb, write_glb, accessor_array  # noqa: E402
d, b = read_glb(Path(sys.argv[1])); node = next(n for n in d['nodes'] if n.get('name') == 'Body'); base = d['meshes'][node['mesh']]
pos = np.concatenate([accessor_array(d, b, p['attributes']['POSITION']) for p in base['primitives']])
normal = np.concatenate([accessor_array(d, b, p['attributes']['NORMAL']) for p in base['primitives']])
normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-9); tree = cKDTree(pos); report = {}
for level, mi in enumerate(base['extras']['openyamm_shadow_lods']):
    if not level:
        continue
    for p in d['meshes'][mi]['primitives']:
        ai = p['attributes']['POSITION']; a = d['accessors'][ai]; v = d['bufferViews'][a['bufferView']]; assert v.get('byteStride', 12) == 12
        assert sum(q['attributes']['POSITION'] == ai for m in d['meshes'] for q in m['primitives']) == 1
        x = accessor_array(d, b, ai); _, nn = tree.query(x); n = normal[nn]; dist = np.einsum('ij,ij->i', x - pos[nn], n)
        push = np.clip(dist + {1: .002, 2: .004, 3: .007}[level], 0, .015); x = x - n * push[:, None]
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0); b[off:off + x.nbytes] = x.astype(np.float32).tobytes()
        a['min'] = x.min(0).tolist(); a['max'] = x.max(0).tolist(); report[str(level)] = {'vertices': len(x), 'maximum_push_metres': float(push.max())}
write_glb(Path(sys.argv[2]), d, b); print('SHRUNK', json.dumps(report))
