"""Local Laplacian smoothing in spheres on the unioned skin (before the rig): the master's knee lumps read as growths in a
crouch, the crotch seam left a spike, and the feet had toes pointing back. Mirrored to both sides when x != 0. Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
SPHERES = [((0.52, -0.25, -0.53), 0.13, 60), ((0.0, 0.0, -0.40), 0.14, 30), ((0.50, 0.12, -0.97), 0.16, 30)]   # + the heel's backward toes (Meshy's star foot) into a round heel     # centre, radius, iterations
bpy.ops.wm.open_mainfile(filepath=IN)
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
P = np.array([v.co[:] for v in bm.verts])
nb = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
# feet: Meshy made a star of toes all round the ankle; MM9's foot is a fin spreading forward. Around the ankle centre, the
# radial reach beyond the ankle wall is kept in front (|angle from forward| < A0) and shortened to KB at the back (A1 and beyond).
def _ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
A0, A1, KB, RA = np.radians(55), np.radians(120), 0.28, 0.17
for sx in (1, -1):
    ring = (np.sign(P[:, 0]) == sx) & (np.abs(P[:, 0]) > 0.15) & (P[:, 2] > -0.87) & (P[:, 2] < -0.83)
    c = P[ring][:, :2].mean(0)
    m = (np.sign(P[:, 0]) == sx) & (np.abs(P[:, 0]) > 0.15) & (P[:, 2] < -0.83)
    d = P[m, :2] - c; r = np.linalg.norm(d, axis=1); phi = np.abs(np.arctan2(d[:, 0], -d[:, 1]))
    k = 1 - (1 - KB) * _ss(phi, A0, A1)
    fz = 1 - _ss(P[m, 2], -0.93, -0.84)
    rn = np.where(r > RA, RA + (r - RA) * k, r)
    rn = r + fz * (rn - r)
    P[m, :2] = c + d * (rn / np.maximum(r, 1e-9))[:, None]
    print('HEEL', sx, c.round(3), int(m.sum()))
for c, r, it in SPHERES:
    for sx in ((1, -1) if c[0] != 0 else (1,)):
        cc = np.array(c) * [sx, 1, 1]
        d = np.linalg.norm(P - cc, axis=1); ids = np.nonzero(d < r)[0]
        w = (1 - (d[ids] / r) ** 2) ** 2
        for _ in range(it):
            avg = np.array([P[nb[i]].mean(0) for i in ids])
            P[ids] = P[ids] + 0.5 * w[:, None] * (avg - P[ids])
        print('SMOOTH', cc.round(2), len(ids))
for v, p in zip(bm.verts, P): v.co = Vector(p)
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
