"""Dumps the LOD0 body primitive ('Elf') of the installed m322 GLB for the UV work: positions, normals, UVs, joints,
weights, triangles, welded vertex ids (exact positions), joint names, the approved head-set faces (right half of the
2080x1024 body | head atlas) and per-face production pieces (Smart Topology shells of ../mm7_m322_claude/work/rig_v6.blend
as dumped by ../mm7_m322_reduce_claude/work/prod_pieces.npz, nearest rest vertex, majority per face):
0 skin shell (body, head, vest, trousers, bracers, boots), 1 hair, 2/3 hands, 4/5 eyes, 8/9/11 mouth bits, other small.
Usage: dump_lod0.py <glb> <out npz>"""
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from glb import Glb

HERE = Path(__file__).resolve().parents[1]
g = Glb(sys.argv[1])
doc = g.doc
mesh = next(m for m in doc['meshes'] if m['name'] == 'Elf')
pr = mesh['primitives'][0]
at = pr['attributes']
pos = g.accessor(at['POSITION']).astype(np.float64)
uv = g.accessor(at['TEXCOORD_0']).astype(np.float64)
tri = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
_, weld = np.unique(pos.round(7), axis=0, return_inverse=True)
weld = weld.ravel()
head_face = uv[tri, 0].mean(1) > 0.5
joints = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
P = np.load(HERE.parent / 'mm7_m322_reduce_claude' / 'work' / 'prod_pieces.npz')
co = np.stack([P['co'][:, 0], P['co'][:, 2], -P['co'][:, 1]], 1)          # Blender Z-up -> glTF Y-up
dist, idx = cKDTree(co).query(pos)
vp = P['piece'][idx]
piece = np.array([np.bincount(vp[t]).argmax() for t in tri])
np.savez(sys.argv[2], pos=pos, nrm=g.accessor(at['NORMAL']), uv=uv, joints=g.accessor(at['JOINTS_0']),
         weights=g.accessor(at['WEIGHTS_0']), tri=tri, weld=weld, head_face=head_face, piece=piece,
         joint_names=np.array(joints))
print('verts', len(pos), 'welded', weld.max() + 1, 'tris', len(tri), 'head faces', int(head_face.sum()),
      'piece map max mm', round(float(dist.max()) * 1000, 3))
print('pieces (all / head set):', {int(k): (int((piece == k).sum()), int((piece[head_face] == k).sum()))
                                   for k in np.unique(piece)[:14]})
