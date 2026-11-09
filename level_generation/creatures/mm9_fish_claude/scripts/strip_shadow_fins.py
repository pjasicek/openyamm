#!/usr/bin/env python3
"""Drop the fin leaves from the fish's dedicated shadow meshes. The engine requires shadow LODs to be opaque, so a
merged shadow mesh cannot carry the fins' alpha cut-out and would cast their square grid cells: every shadow triangle
with a vertex weighted more than 5 % to a fin joint goes (the buried root band, pure body weight, stays inside the body
and casts nothing visible). The fins themselves still draw; they cast no shadow.
Usage: strip_shadow_fins.py in.glb out.glb <mesh node>"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shrink_shadow_lods import read_glb, write_glb, view, THIN

src, dst, node_name = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
doc, binary = read_glb(src)
node = next(n for n in doc['nodes'] if n.get('name') == node_name)
shadows = doc['meshes'][node['mesh']]['extras']['openyamm_shadow_lods']
joints = doc['skins'][0]['joints']
thin = np.array([doc['nodes'][j].get('name') in THIN for j in joints])
report = {}
for mi in shadows:
    for p in doc['meshes'][mi]['primitives']:
        jn = view(doc, binary, p['attributes']['JOINTS_0'])[0].astype(int).copy()
        wt = view(doc, binary, p['attributes']['WEIGHTS_0'])[0].astype(np.float64).copy()
        finw = (wt * thin[jn]).sum(1)
        acc = doc['accessors'][p['indices']]
        idx = view(doc, binary, p['indices'])[0].reshape(-1, 3).astype(np.int64).copy()
        keep = idx[(finw[idx] <= 0.05).all(1)]
        packed = keep.astype(np.uint32).tobytes()
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(packed),
                                   'target': 34963})
        binary += packed
        doc['accessors'].append({'bufferView': len(doc['bufferViews']) - 1, 'componentType': 5125,
                                 'count': int(keep.size), 'type': 'SCALAR'})
        p['indices'] = len(doc['accessors']) - 1
        report[doc['meshes'][mi].get('name')] = [len(idx), len(keep)]
write_glb(dst, doc, binary)
print('SHADOW FINS', json.dumps(report))
