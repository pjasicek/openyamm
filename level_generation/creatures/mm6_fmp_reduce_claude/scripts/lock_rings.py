"""Add the faces within N edge rings of given source vertices to a keep array (geometric drift lock).
Usage: lock_rings.py <keep in .npy> <verts .npy>[,<verts .npy>] <rings> <keep out .npy>"""
import sys, numpy as np
d = np.load('work/mesh_in.npz'); faces = d['faces']
keep = np.load(sys.argv[1]).copy(); vs = set(np.concatenate([np.load(p) for p in sys.argv[2].split(',')]).tolist())
for _ in range(int(sys.argv[3])):
    hit = np.isin(faces, list(vs)).any(1); vs |= set(faces[hit].ravel().tolist())
hit = np.isin(faces, list(vs)).any(1)
print('lock', hit.sum(), 'new', (hit & ~keep).sum()); keep |= hit; np.save(sys.argv[4], keep)
