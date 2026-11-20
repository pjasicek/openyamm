"""Boundary and non-manifold edges of 'Body': count, and distance to the nearest eye-sphere centre (piece 1).
Args: <blend>"""
import bpy, bmesh, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me = bpy.data.objects['Body'].data
piece = np.array([d.value for d in me.attributes['piece'].data])
P = np.array([tuple(v.co) for v in me.vertices])
eyes = []
for sgn in (1, -1):
    s = P[(piece == 1) & (np.sign(P[:, 0]) == sgn)]
    eyes.append((s.mean(0), np.linalg.norm(s - s.mean(0), axis=1).max()))
bm = bmesh.new(); bm.from_mesh(me)
for kind, es in (('boundary', [e for e in bm.edges if e.is_boundary]), ('nonmanifold', [e for e in bm.edges if len(e.link_faces) > 2])):
    pts = np.array([tuple((e.verts[0].co + e.verts[1].co) / 2) for e in es])
    if len(pts):
        d = np.min([np.linalg.norm(pts - c, axis=1) / r for c, r in eyes], axis=0)
        print('DEFECT', kind, len(es), 'inside eye spheres', int((d < 1).sum()), 'outside at', pts[d >= 1].round(4).tolist()[:12])
