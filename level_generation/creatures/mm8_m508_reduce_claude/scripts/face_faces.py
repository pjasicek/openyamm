#!/usr/bin/env python3
"""Faces of the Air Elemental's face for REA_PROTECT_FACES: Head-dominated faces (dump_mesh.py's protect flag) in front
of the skull's centre, down through the jaw and the front of the neck (a cut below the chin smeared the dark
under-chin shading up into a wedge). The body's baked colour carries the face's shading; a 50 % cut
interpolates it across larger triangles and the brow, eye sockets and jaw turn blocky.
Usage: face_faces.py [forward offset m, default 0] [drop m, default 0] -> work/face_faces.npy"""
import sys
import numpy as np

OFF = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
DROP = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0   # leave out head faces this far above its lowest point
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']
head = d['protect'] > .5; cen = v[f].mean(1)
c = cen[head].mean(0)                       # Blender coords: -Y is forward, Z up
face = head & (cen[:, 1] < c[1] - OFF) & (cen[:, 2] > cen[head, 2].min() + DROP)
np.save('work/face_faces.npy', face)
print('FACE', int(face.sum()), 'of', int(head.sum()), 'head faces; head centre', np.round(c, 3))
