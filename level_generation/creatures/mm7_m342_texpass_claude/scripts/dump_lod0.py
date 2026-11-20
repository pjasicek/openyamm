"""Dumps the LOD0 body primitive of the installed m342 GLB for the UV work: positions, normals, UVs, joints, weights,
triangles, welded vertex ids (exact positions), joint names, the approved head-set faces (the right half of the
2080x1024 body | head atlas), connected pieces of the welded surface and the hidden-leg faces (the legs above the shoes
share one UV point of the petticoat: zero UV area in the installed atlas). Usage: dump_lod0.py <glb> <out npz>"""
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from glb import Glb

g = Glb(sys.argv[1])
doc = g.doc
mesh = next(m for m in doc['meshes'] if m['name'] == 'M342')
pr = mesh['primitives'][0]
at = pr['attributes']
pos = g.accessor(at['POSITION']).astype(np.float64)
uv = g.accessor(at['TEXCOORD_0']).astype(np.float64)
tri = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
_, weld = np.unique(pos.round(7), axis=0, return_inverse=True)
weld = weld.ravel()
head_face = uv[tri, 0].mean(1) > 0.5
wt = weld[tri]
n = int(weld.max()) + 1
e = np.concatenate([wt[:, [0, 1]], wt[:, [1, 2]], wt[:, [2, 0]]])
_, vpiece = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
piece = vpiece[wt[:, 0]]
u = uv[tri]
uv_area = np.abs((u[:, 1, 0] - u[:, 0, 0]) * (u[:, 2, 1] - u[:, 0, 1]) - (u[:, 2, 0] - u[:, 0, 0]) * (u[:, 1, 1] - u[:, 0, 1])) / 2
leg_face = (uv_area < 1e-10) & ~head_face
joints = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
np.savez(sys.argv[2], pos=pos, nrm=g.accessor(at['NORMAL']), uv=uv, joints=g.accessor(at['JOINTS_0']),
         weights=g.accessor(at['WEIGHTS_0']), tri=tri, weld=weld, head_face=head_face, piece=piece, leg_face=leg_face,
         joint_names=np.array(joints))
print('verts', len(pos), 'welded', n, 'tris', len(tri), 'head faces', int(head_face.sum()), 'pieces', piece.max() + 1,
      'zero-uv (leg) faces', int(leg_face.sum()), 'zero-uv head faces', int(((uv_area < 1e-10) & head_face).sum()))
