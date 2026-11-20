"""Curvature-adaptive isotropic remeshing (MeshLab, via pymeshlab) of the exported Wyrm body triangles: even,
well-shaped triangles, smaller on curved features (spines, toes, claws, horns, mouth), larger on the smooth trunk,
sharp feature edges kept, and every vertex held within maxsurfdist of the original surface. One continuous surface:
no original pieces layered on top. Usage: remesh_ml.py <work dir> <tag> <target edge % of bbox> <max dist %>
Reads work/body_in.npz, writes work/body_<tag>.npz (triangles padded to 4 indices for retopo.py)."""
import sys
import numpy as np
import pymeshlab as ml

work, tag, target, maxdist = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
d = np.load(f'{work}/body_in.npz')
ms = ml.MeshSet()
ms.add_mesh(ml.Mesh(vertex_matrix=d['verts'].astype(np.float64), face_matrix=d['faces'].astype(np.int32)))
ms.meshing_remove_duplicate_vertices()
ms.meshing_isotropic_explicit_remeshing(iterations=12, adaptive=True, targetlen=ml.PercentageValue(target),
                                        featuredeg=35.0, checksurfdist=True, maxsurfdist=ml.PercentageValue(maxdist),
                                        splitflag=True, collapseflag=True, swapflag=True, smoothflag=True,
                                        reprojectflag=True)
m = ms.current_mesh()
v, f = m.vertex_matrix(), m.face_matrix()
np.savez(f'{work}/body_{tag}.npz', verts=v.astype(np.float32),
         faces=np.concatenate([f, f[:, 2:3]], axis=1).astype(np.int64))
print('REMESHED', tag, len(v), 'verts', len(f), 'tris')
