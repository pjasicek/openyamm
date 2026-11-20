"""Instant Meshes (Jakob et al. 2015, via PyNanoInstantMeshes) on the exported Wyrm body triangles.
Usage (outside Blender, in a venv with pynanoinstantmeshes): remesh_im.py <work dir> <tag> <target vertices>
Reads work/body_in.npz, writes work/body_<tag>.npz (quad-dominant faces; triangles padded as (a, b, c, c))."""
import sys
import numpy as np
import pynanoinstantmeshes as nim

work, tag, target = sys.argv[1], sys.argv[2], int(sys.argv[3])
d = np.load(f'{work}/body_in.npz')
v, f = nim.remesh(d['verts'].astype(np.float32), d['faces'].astype(np.uint32), target, rosy=4, posy=4,
                  creaseAngle=0.0, align_to_boundaries=True, extrinsic=True, smooth_iter=2, deterministic=True)
faces = [tuple(int(i) for i in q if i != np.uint32(0xFFFFFFFF)) for q in f]
faces = [q[:3] if (len(q) == 4 and q[3] == q[2]) else q for q in faces]
np.savez(f'{work}/body_{tag}.npz', verts=np.asarray(v, np.float32), faces=np.array([q + (q[-1],) * (4 - len(q)) for q in faces], np.int64))
print('REMESHED', tag, len(v), 'verts', len(faces), 'faces')
