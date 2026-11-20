"""Final mouth geometry (orchestrator r5, 2026-11-02): one closed mouth with a shallow groove and clean, even, symmetric lip
edges, made BEFORE the fresh head paints (so the paint is made for this shape).

Input: the closed master (mouth_close_pm3.py: interior 1.5 mm behind the lips) and the master before the close (to know which
vertices are the groove: the ones that moved). The lip-edge vertices are the unmoved head vertices sharing an edge with a groove
vertex; above the groove's local height they are the upper lip's edge, below it the lower lip's. Per edge, height and depth are
fitted as symmetric even polynomials about the mouth's midline x0 (z = a + b u^2 + c u^4, y likewise, u = x - x0, fitted on
both halves together, so left and right match), then:
  groove vertices   z = mid(u) (the mean of the two edge curves), y as they are (1.5 mm behind the lips)
  upper edge        z = mid(u) + GAP/2, y = its fitted depth curve
  lower edge        z = mid(u) - GAP/2, y = its fitted depth curve
so the lips meet on one smooth curve with a GAP-wide shallow groove. Positions only (faces, UVs, weights unchanged).
Args (Blender): <closed blend> <reference blend (before close)> <out blend> [gap 0.0008] [x0 -0.003]"""
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, REF, OUT = a[:3]
GAP = float(a[3]) if len(a) > 3 else 0.0008
X0 = float(a[4]) if len(a) > 4 else -0.003
bpy.ops.wm.open_mainfile(filepath=REF)
P0 = np.array([v.co[:] for v in bpy.data.objects['Body'].data.vertices])
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
P = np.array([v.co[:] for v in me.vertices])
assert len(P) == len(P0), 'reference must have the same vertices'
hf = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hf)
head = np.zeros(len(P), bool)
for p in me.polygons:
    if hf[p.index]:
        head[list(p.vertices)] = True
box = head & (np.abs(P[:, 0] - X0) < 0.034) & (P[:, 2] > 0.732) & (P[:, 2] < 0.765) & (P[:, 1] < -0.03)
groove = box & (np.linalg.norm(P - P0, axis=1) > 1e-6)
adj = {}
for e in me.edges:
    i, j = e.vertices
    adj.setdefault(i, set()).add(j); adj.setdefault(j, set()).add(i)
gi = np.nonzero(groove)[0]
edge = [v for v in np.nonzero(box & ~groove)[0] if adj.get(v, set()) & set(gi.tolist())]
edge = np.array(edge)


def local_mid(v):
    near = gi[np.abs(P[gi, 0] - P[v, 0]) < 0.004]
    return P[near, 2].mean() if len(near) else P[gi, 2].mean()


mids = np.array([local_mid(v) for v in edge])
upper = edge[P[edge, 2] >= mids]; lower = edge[P[edge, 2] < mids]


UW = 0.022     # fit and full correction inside |u| < UW; faded out to 0 at UW + 0.008 (the corners keep their shape)
upper_f = upper[np.abs(P[upper, 0] - X0) < UW]; lower_f = lower[np.abs(P[lower, 0] - X0) < UW]


def fit(idx, k):
    u = P[idx, 0] - X0
    A = np.column_stack([np.ones_like(u), u ** 2, u ** 4])
    c, *_ = np.linalg.lstsq(A, P[idx, k], rcond=None)
    return lambda x: np.column_stack([np.ones_like(x), (x - X0) ** 2, (x - X0) ** 4]) @ c


zu, zl, yu, yl = fit(upper_f, 2), fit(lower_f, 2), fit(upper_f, 1), fit(lower_f, 1)
mid = lambda x: 0.5 * (zu(x) + zl(x))
newP = P.copy()
newP[gi, 2] = mid(P[gi, 0])
newP[upper, 2] = mid(P[upper, 0]) + GAP / 2; newP[upper, 1] = yu(P[upper, 0])
newP[lower, 2] = mid(P[lower, 0]) - GAP / 2; newP[lower, 1] = yl(P[lower, 0])
# the groove stays behind both lips
lipfront = np.maximum(yu(P[gi, 0]), yl(P[gi, 0]))
newP[gi, 1] = np.maximum(newP[gi, 1], lipfront + 0.0012)
# fade toward the corners and cap every move at 3 mm (r5: an extrapolated corner vertex moved 26 mm and drew a sliver)
uu = np.abs(P[:, 0] - X0)
fade = np.clip(1 - (uu - UW) / 0.008, 0, 1)[:, None]
d = (newP - P) * fade
n = np.linalg.norm(d, axis=1, keepdims=True)
d *= np.minimum(1, 0.003 / np.maximum(n, 1e-9))
newP = P + d
rep = dict(groove=int(len(gi)), upper=int(len(upper)), lower=int(len(lower)),
           max_move_mm=round(float(np.linalg.norm(newP - P, axis=1).max()) * 1000, 2),
           upper_z_resid_mm=round(float(np.abs(P[upper_f, 2] - zu(P[upper_f, 0])).max()) * 1000, 2),
           lower_z_resid_mm=round(float(np.abs(P[lower_f, 2] - zl(P[lower_f, 0])).max()) * 1000, 2))
me.vertices.foreach_set('co', newP.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('LIPEDGE ' + json.dumps(rep))
