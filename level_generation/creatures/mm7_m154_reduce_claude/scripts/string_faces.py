#!/usr/bin/env python3
"""Bowstring faces per colour/shadow LOD of a body GLB: triangles whose three vertices are weighted only to the Bow and
StringNock joints (the 6-sided string tube), with their bounds. Usage: string_faces.py <glb> [mesh node, default M154]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
d, b = read_glb(Path(sys.argv[1])); NODE = sys.argv[2] if len(sys.argv) > 2 else 'M154'
node = next(n for n in d['nodes'] if n.get('name') == NODE); names = [d['nodes'][i]['name'] for i in d['skins'][node['skin']]['joints']]
sj = [names.index('Bow'), names.index('StringNock')]
ex = d['meshes'][node['mesh']]['extras']; chain = [node['mesh']] + ex['openyamm_lods'] + ex.get('openyamm_shadow_lods', [])
arr = lambda i: np.frombuffer(accessor_bytes(d, b, i), {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}[d['accessors'][i]['componentType']])
for mi in chain:
    p = d['meshes'][mi]['primitives'][0]; a = p['attributes']; n = d['accessors'][a['POSITION']]['count']
    w = np.zeros(n)
    for k in [x for x in a if x.startswith('JOINTS_')]:
        J = arr(a[k]).reshape(n, 4).astype(int); W = arr(a['WEIGHTS_' + k[7:]]).reshape(n, 4).astype(float)
        w += (W * np.isin(J, sj)).sum(1)
    F = arr(p['indices']).reshape(-1, 3); s = (w[F] > 0.999).all(1); P = arr(a['POSITION']).reshape(n, 3)
    print(d['meshes'][mi]['name'], 'tris', len(F), 'string tris', int(s.sum()),
          'string verts bounds', (P[np.unique(F[s])].min(0).round(3).tolist(), P[np.unique(F[s])].max(0).round(3).tolist()) if s.any() else '-')
