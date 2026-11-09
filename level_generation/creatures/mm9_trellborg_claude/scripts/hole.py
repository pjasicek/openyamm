"""Largest free cylinder through the fist along the knuckle line, each hand, bind pose. Args: blend json"""
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
J = json.load(open(a[1]))
print('KEYS', list(J.keys())[:8])
P = np.array([v.co[:] for v in me.vertices])
for S, sg in (('L', 1), ('R', -1)):
    j = J['joints'][S]
    I, M, Pk = np.array(j['finger2-1']), np.array(j['finger3-1']), np.array(j['finger5-1'])
    kn = (I - Pk) / np.linalg.norm(I - Pk)
    tipM = np.array(j['finger3-3_tip'])
    c0 = 0.5 * (I + Pk)
    Q = P[np.linalg.norm(P - c0, axis=1) < 0.2]; ax = (Q - c0) @ kn
    Q = Q[np.abs(ax - 0.0) < 0.075]
    e1 = np.cross(kn, [0.3, 0.2, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(kn, e1)
    q2 = np.c_[(Q - c0) @ e1, (Q - c0) @ e2]
    best = (0, None)
    for u in np.arange(-0.12, 0.12, 0.003):
        for v in np.arange(-0.12, 0.12, 0.003):
            d = np.hypot(q2[:, 0] - u, q2[:, 1] - v)
            # enclosed: there must be verts all round
            ang = np.arctan2(q2[:, 1] - v, q2[:, 0] - u)[d < 0.07]
            cov = len(np.unique((ang // 0.52).astype(int))) if len(ang) else 0
            if cov >= 8 and d.min() > best[0]: best = (float(d.min()), (u, v), cov)
    print('HOLE', S, 'r', round(best[0], 4), 'cover', best[2] if best[1] else None, 'centre', np.round(c0 + e1 * best[1][0] + e2 * best[1][1], 3).tolist(), 'kn', np.round(kn, 3).tolist())
