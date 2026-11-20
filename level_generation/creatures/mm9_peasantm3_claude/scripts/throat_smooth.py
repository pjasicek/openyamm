"""Even throat surface (orchestrator review of r6: lighter flat rectangles across the throat). Head-set vertices of the throat
(rest z between the neckline + 3 mm and the jaw line - 6 mm, i.e. below the beard; the front 200 degrees about the neck axis)
are Laplacian-smoothed (ITER passes, factor 0.5) with every vertex outside the zone fixed, so the facets that caught the light as
separate planes blend into one surface. Not the face, nose, lips or beard (the Wyrde rule). Positions only.
Args (Blender): <in blend> <out blend> [iter 12]"""
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
ITER = int(a[2]) if len(a) > 2 else 12
Z0, Y0, SLOPE, CURVE, YB, BACK, ZMAX = 0.676, -0.035, 0.45, 1.2, 0.0, 0.4, 0.725   # face_rigid_pm3.py jaw line
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data; rig = body.parent
nb = rig.data.bones['Bip01 Neck']; C = np.array((rig.matrix_world @ nb.head_local)[:2])
P = np.array([v.co[:] for v in me.vertices])
hf = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hf)
head = np.zeros(len(P), bool)
for p in me.polygons:
    if hf[p.index]:
        head[list(p.vertices)] = True
d = P[:, :2] - C; r = np.hypot(d[:, 0], d[:, 1]); ang = np.degrees(np.arctan2(d[:, 0], -d[:, 1]))
zb = np.minimum(Z0 + SLOPE * (P[:, 1] - Y0) + CURVE * P[:, 0] ** 2 + BACK * np.clip(P[:, 1] - YB, 0, None), ZMAX)
zone = head & (r < 0.12) & (np.abs(ang) < 100) & (P[:, 2] > 0.672) & (P[:, 2] < zb - 0.006)
adj = {}
for e in me.edges:
    i, j = e.vertices
    adj.setdefault(i, []).append(j); adj.setdefault(j, []).append(i)
idx = np.nonzero(zone)[0]
Q = P.copy()
for _ in range(ITER):
    cur = Q.copy()
    for i in idx:
        nbr = adj.get(i, [])
        if nbr:
            Q[i] = cur[i] + 0.5 * (cur[nbr].mean(0) - cur[i])
me.vertices.foreach_set('co', Q.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('THROATSMOOTH ' + json.dumps({'verts': int(len(idx)), 'max_move_mm': round(float(np.linalg.norm(Q - P, axis=1).max()) * 1000, 2)}))
