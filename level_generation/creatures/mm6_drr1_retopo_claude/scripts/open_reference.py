"""Spike-free reference surface by morphological opening (MeshLab offset surfaces): erode the remeshed body by R,
then dilate by R. Features thinner than about 2R (spines, horns, tail spikes) vanish; the thick body returns.
Usage: open_reference.py <work dir> <tag> <R metres> -> work/body_<tag>_open.npz"""
import sys
import numpy as np
import pymeshlab as ml

work, tag, r = sys.argv[1], sys.argv[2], float(sys.argv[3])
d = np.load(f'{work}/body_{tag}.npz')
faces = np.array([f[:3] for f in d['faces']], np.int32)
ms = ml.MeshSet()
ms.add_mesh(ml.Mesh(vertex_matrix=d['verts'].astype(np.float64), face_matrix=faces))
cell = ml.PureValue(0.002)
ms.generate_resampled_uniform_mesh(cellsize=cell, offset=ml.PureValue(-r), absdist=False, mergeclosevert=True)
ms.generate_resampled_uniform_mesh(cellsize=cell, offset=ml.PureValue(r), absdist=False, mergeclosevert=True)
m = ms.current_mesh()
np.savez(f'{work}/body_{tag}_open.npz', verts=m.vertex_matrix().astype(np.float32),
         faces=np.concatenate([m.face_matrix(), m.face_matrix()[:, 2:3]], axis=1).astype(np.int64))
print('OPENED', tag, r, m.vertex_number(), 'verts', m.face_number(), 'faces')
