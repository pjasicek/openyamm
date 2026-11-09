"""Dumps the LOD0 body primitive of the installed Mage GLB (mm7_m274) for the UV work: positions, normals, UVs,
joints, weights, triangles, welded vertex ids (exact positions), joint names and the approved head-set faces (the right
half of the 2080x1024 body | head atlas: face, scalp, ears, beard, braids). Usage: dump_lod0.py <glb> <out npz>"""
import sys
import numpy as np
from glb import Glb

g = Glb(sys.argv[1])
doc = g.doc
mesh = next(m for m in doc['meshes'] if m['name'] == 'M274')
pr = mesh['primitives'][0]
at = pr['attributes']
pos = g.accessor(at['POSITION']).astype(np.float64)
uv = g.accessor(at['TEXCOORD_0']).astype(np.float64)
tri = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
_, weld = np.unique(pos.round(7), axis=0, return_inverse=True)
weld = weld.ravel()
head_face = uv[tri, 0].mean(1) > 0.5
joints = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
np.savez(sys.argv[2], pos=pos, nrm=g.accessor(at['NORMAL']), uv=uv, joints=g.accessor(at['JOINTS_0']),
         weights=g.accessor(at['WEIGHTS_0']), tri=tri, weld=weld, head_face=head_face, joint_names=np.array(joints))
print('verts', len(pos), 'welded', weld.max() + 1, 'tris', len(tri), 'head faces', int(head_face.sum()),
      'u range body', uv[tri[~head_face], 0].min(), uv[tri[~head_face], 0].max(),
      'head', uv[tri[head_face], 0].min(), uv[tri[head_face], 0].max())
