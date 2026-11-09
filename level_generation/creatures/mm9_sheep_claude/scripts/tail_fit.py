"""Pose the Meshy tail onto MM9's tail (after fit_quad.py) and mark it as chain 4 for rig_body.py.

The Meshy tail sticks up and back from the rump; MM9's hangs back and down from Xtail. The tail is the part of the
mesh within a geodesic distance of its tip where the cross-section stays thin (it widens sharply where the tail joins
the rump). It is turned rigidly about its base onto MM9's tail axis (Xtail head -> the farthest MM9 tail vertex) and
its base moved to Xtail, blended into the rump over BLEND metres of surface distance.
Args: <fit blend> <out blend> <report json>"""
import bpy, bmesh, sys, json, heapq, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
BLEND = 0.05
bpy.ops.wm.open_mainfile(filepath=IN)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
me = body.data
P = np.array([tuple(v.co) for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
tail_mm9 = bpy.data.objects['tail.mesh']
TP = np.array([tuple(tail_mm9.matrix_world @ v.co) for v in tail_mm9.data.vertices])
root = np.array(arm.data.bones['Xtail'].head_local)
root = np.array(tuple(arm.matrix_world @ Vector(root)))
tip_mm9 = TP[np.argmax(np.linalg.norm(TP - root, axis=1))]
nbr = [[] for _ in range(len(P))]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
cand = np.nonzero((piece == 0) & (P[:, 1] > root[1] - 0.05))[0]
cand = cand[P[cand, 2] > 0.45]
tip = int(cand[np.argmax(P[cand, 1])])


def geodesic(src):
    dist = {src: 0.0}; pq = [(0.0, src)]
    while pq:
        d, i = heapq.heappop(pq)
        if d > dist[i] or d > 0.6:
            continue
        for j in nbr[i]:
            nd = d + float(np.linalg.norm(P[i] - P[j]))
            if nd < dist.get(j, 1e9):
                dist[j] = nd; heapq.heappush(pq, (nd, j))
    return dist


gd = geodesic(tip)
ids = np.array(list(gd)); dd = np.array([gd[i] for i in ids])
# cross-section radius per 1 cm geodesic band: the base is where it jumps
bands = []
for k in range(0, 40):
    m = (dd >= k * 0.01) & (dd < (k + 1) * 0.01)
    if m.sum() < 3:
        bands.append(None); continue
    c = P[ids[m]].mean(0)
    bands.append(float(np.linalg.norm(P[ids[m]] - c, axis=1).mean()))
rads = [b for b in bands if b is not None]
ref = np.median(rads[1:5])
base_k = next(k for k in range(3, 40) if bands[k] is not None and bands[k] > 1.8 * ref)
d_base = base_k * 0.01
tail_ids = ids[dd < d_base]
ring = ids[(dd >= d_base - 0.01) & (dd < d_base)]
base_c = P[ring].mean(0)
tail_axis = P[tip] - base_c
tgt_axis = tip_mm9 - root
q = Vector(tail_axis).rotation_difference(Vector(tgt_axis))
import os
TURN = float(os.environ.get('TAIL_TURN', '0'))   # 0: keep the Meshy tail (it already hangs back/down like MM9's)
q = Quaternion().slerp(q, TURN)
R = np.array(q.to_matrix())
# keep the Meshy tail length, place its base at Xtail (partly: the base sits on our rump surface)
base_new = base_c + TURN * 0.6 * (root - base_c)
w = np.zeros(len(P))
for i, d in gd.items():
    if d < d_base:
        w[i] = 1.0
    elif d < d_base + BLEND:
        t = 1 - (d - d_base) / BLEND
        w[i] = t * t * (3 - 2 * t)
for i in np.nonzero(w > 0)[0]:
    p_rigid = base_new + R @ (P[i] - base_c)
    me.vertices[i].co = Vector(tuple(P[i] * (1 - w[i]) + p_rigid * w[i]))
chain = me.attributes['chain']
for i in np.nonzero(w > 0.5)[0]:
    chain.data[int(i)].value = 4
rep = {'bands_cm_radius': [round(b, 3) if b else None for b in bands[:20]], 'tip': P[tip].round(3).tolist(), 'base_band_cm': base_k, 'band_radius_ref': ref, 'tail_verts': int(len(tail_ids)),
       'turn_deg': math.degrees(q.angle), 'tail_len': float(np.linalg.norm(tail_axis)),
       'mm9_len': float(np.linalg.norm(tgt_axis)), 'base_move': float(np.linalg.norm(base_new - base_c))}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('TAIL ' + json.dumps(rep))
