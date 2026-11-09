"""Smooth the eye-socket ring of the head shell (face fix, 2026-11-01; user: "2 eyebrows? and like weird eye area?").
Meshy carved a ledge round each eye (the socket ring and lid step, left after eye_fill.py); lit from above its top edge
shades as a light, sharply outlined band under the brows. Taubin smoothing (lambda 0.5 / mu -0.53, ITER passes) of the
head-shell vertices in the eye window (|x| < 7 cm, rest z 0.757-0.835, the front of the face), weighted 1 inside and
eased to 0 over the window's last 1.2 cm, so nothing outside moves. Only positions change: UVs, weights and topology
stay, so the paints stay valid. Args (Blender): <in blend> <out blend> [iterations 12]"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
ITER = int(a[2]) if len(a) > 2 else 12
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
me = body.data
hd = np.zeros(len(me.polygons), np.int32)
me.attributes['head'].data.foreach_get('value', hd)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
head_v = {v.index for f in bm.faces if hd[f.index] for v in f.verts}
CO = np.array([v.co[:] for v in bm.verts])


def ss(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


x, y, z = CO[:, 0], CO[:, 1], CO[:, 2]
E = 0.012
w = ss((0.07 - np.abs(x)) / E) * ss((z - 0.757) / E) * ss((0.835 - z) / E) * ss((-y - 0.06) / E)
w[[i for i in range(len(CO)) if i not in head_v]] = 0
idx = np.nonzero(w > 0)[0]
nbr = {i: [e.other_vert(bm.verts[i]).index for e in bm.verts[i].link_edges] for i in idx}
P = CO.copy()
for it in range(ITER):
    for lam in (0.5, -0.53):
        L = np.array([P[nbr[i]].mean(0) - P[i] if nbr[i] else np.zeros(3) for i in idx])
        P[idx] += lam * w[idx, None] * L
moved = np.linalg.norm(P - CO, axis=1)
for i in idx:
    bm.verts[i].co = P[i]
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('EYESMOOTH', json.dumps({'verts': int(len(idx)), 'iterations': ITER, 'max_move_mm': round(float(moved.max()) * 1000, 2),
                              'mean_move_mm': round(float(moved[idx].mean()) * 1000, 2)}))
