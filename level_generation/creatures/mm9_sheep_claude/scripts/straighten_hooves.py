"""Straighten the hooves in the bind pose (user 2026-10-30: "feet angled a bit"). The Meshy hooves came from a stance that
the limb fit turned: the soles tilt (front 10 deg outer edge down, 8.6 deg toe up; hind 5.6 and 3.6) and the hind toes point
18 deg outward, while MM9's hooves are level diamonds pointing straight forward. Each hoof is turned rigidly about its
centroid (sole levelled, then the given yaw) with a ramp up the pastern; the mesh stays mirror-exact, topology, UVs and
weights are unchanged, so the paint stays valid. Clips are untouched.
Args: <in blend> <out blend> <front yaw deg> <hind yaw deg> (yaw: + turns the toe inward)"""
import bpy, sys, json, math
import numpy as np
from mathutils import Matrix, Vector
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, YF, YH = argv[0], argv[1], float(argv[2]), float(argv[3])
Z0, Z1 = 0.072, 0.135
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Body']; me = o.data
P = np.array([tuple(v.co) for v in me.vertices])
rep = {}
for name, y0, yaw in (('front', -0.27, YF), ('hind', 0.49, YH)):
    for side in (1, -1):
        sel = (np.hypot(P[:, 0] - side * 0.135, P[:, 1] - y0) < 0.075)
        hoof = sel & (P[:, 2] < 0.06)
        c = P[hoof].mean(0)
        low = P[sel & (P[:, 2] < P[sel, 2].min() + 0.014)]
        A = np.c_[low[:, 0] - low[:, 0].mean(), low[:, 1] - low[:, 1].mean(), np.ones(len(low))]
        gx, gy, _ = np.linalg.lstsq(A, low[:, 2], rcond=None)[0]
        n = Vector((-gx, -gy, 1)).normalized()
        R = n.rotation_difference(Vector((0, 0, 1))).to_matrix()
        Rz = Matrix.Rotation(math.radians(yaw) * side, 3, 'Z')  # + side turns +X hoof's toe (-Y) toward -X... inward
        M = np.array(Rz @ R)
        ids = np.nonzero(sel & (P[:, 2] < Z1))[0]
        for i in ids:
            t = float(np.clip((Z1 - P[i, 2]) / (Z1 - Z0), 0, 1))
            a = t * t * (3 - 2 * t)
            me.vertices[int(i)].co = Vector(tuple(P[i] + a * (M @ (P[i] - c) + c - P[i])))
        rep[f'{name}_{side}'] = {'verts': len(ids), 'tilt_x': round(math.degrees(math.atan(gx)), 1), 'tilt_y': round(math.degrees(math.atan(gy)), 1)}
P2 = np.array([tuple(v.co) for v in me.vertices])
rep['zmin'] = float(P2[:, 2].min())
print('STRAIGHT ' + json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
