"""Spike tips back onto the surface (user review 2026-10-20: a 23 cm sliver ran from the mask across the chest to the right
upper arm, and thinner ones from the mask down the front: Smart Topology spikes that step1_clean.py's cut missed).
A vertex of a sliver face (longest edge > MINLEN, altitude < MAXALT, its normal > 60 deg off a neighbour's) or of a long
face (longest edge > MINLEN and LONG x the median edge around it: the 19 cm triangles bridging the chest to the right
upper arm) on the listed shells is a spike tip when the median length of its edges exceeds TIP x the median edge length
of its neighbours; a tip moves to the mean of its non-tip neighbours. Only rest positions change (no topology, UV,
weight or texture change), so the same pass is run on the gated rig (rig_v5.blend) and the textured master (rig_v6.blend), which share the mesh.
Writes work/despike_moved.json (moved vertex ids, for repaint_moved.py).
Args: -- <in blend> <out blend>   (env PIECES=0 MINLEN=0.025 MAXALT=0.004 LONG=3 TIP=2.5 PASSES=3 FOLD=120)"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
me = bpy.data.objects['Body'].data
PIECES = {int(x) for x in os.environ.get('PIECES', '0').split(',')}
MINLEN, MAXALT = float(os.environ.get('MINLEN', '0.025')), float(os.environ.get('MAXALT', '0.004'))
TIP, PASSES = float(os.environ.get('TIP', '2.5')), int(os.environ.get('PASSES', '3'))
LONG = float(os.environ.get('LONG', '3'))
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
nbr = {}
for e in me.edges:
    i, j = e.vertices; nbr.setdefault(i, set()).add(j); nbr.setdefault(j, set()).add(i)
vf = {}
for p in me.polygons:
    for v in p.vertices:
        vf.setdefault(v, []).append(p.index)
moved = {}
for it in range(PASSES):
    co = np.array([tuple(v.co) for v in me.vertices])
    me.update(); cand = set()
    for p in me.polygons:
        if pv[p.vertices[0]] not in PIECES:
            continue
        P = co[list(p.vertices)]; e = [np.linalg.norm(P[(k + 1) % len(P)] - P[k]) for k in range(len(P))]
        L = max(e)
        if L <= MINLEN:
            continue
        nb = {f for v in p.vertices for f in vf[v]} - {p.index}
        sliver = 2 * p.area / L < MAXALT
        ring = np.median([np.linalg.norm(co[v] - co[n]) for v in p.vertices for n in nbr[v]])
        if L > LONG * ring:                                         # a face bridging two surfaces
            cand.update(p.vertices); continue
        dev = max((np.degrees(np.arccos(np.clip(np.dot(p.normal, me.polygons[f].normal), -1, 1))) for f in nb), default=0)
        if sliver and dev > 60:
            cand.update(p.vertices)
    med = {v: float(np.median([np.linalg.norm(co[v] - co[n]) for n in nbr[v]])) for v in cand}
    tips = set()
    for v in cand:
        ref = np.median([np.median([np.linalg.norm(co[n] - co[m]) for m in nbr[n]]) for n in nbr[v]])
        if med[v] > TIP * ref and med[v] > 0.01:
            tips.add(v)
    if not tips:
        break
    for v in tips:
        ok = [n for n in nbr[v] if n not in tips] or list(nbr[v])
        new = co[ok].mean(0); moved[v] = moved.get(v, 0.0) + float(np.linalg.norm(new - co[v]))
        me.vertices[v].co = tuple(new)
    print(f'DESPIKE pass {it}: {len(cand)} sliver vertices, {len(tips)} tips moved')
me.update()
# unfold: faces of the listed shells folded back against a neighbour (normal over FOLD deg off; a moved tip can leave a
# fold at a junction: user review 2026-10-20, a skin triangle stuck out of the vest at the right biceps) get their
# vertices relaxed toward the mean of their neighbours until none is folded; only within two rings of the moved tips
# (the shell has legitimate folds elsewhere: collar, vest opening, layered flaps)
FOLD = float(os.environ.get('FOLD', '120'))
near = set(moved)
for _ in range(2):
    near |= {n for v in near for n in nbr[v]}
def folded():
    me.update(); out = set()
    for p in me.polygons:
        if pv[p.vertices[0]] not in PIECES or not set(p.vertices) & near:
            continue
        nb = {f for v in p.vertices for f in vf[v]} - {p.index}
        if any(np.degrees(np.arccos(np.clip(np.dot(p.normal, me.polygons[f].normal), -1, 1))) > FOLD for f in nb):
            out.update(set(p.vertices) & near)
    return out
for it in range(30):
    fv = folded()
    if not fv:
        break
    co = np.array([tuple(v.co) for v in me.vertices])
    for v in fv:
        new = co[list(nbr[v])].mean(0); new = co[v] + 0.5 * (new - co[v])
        moved[v] = moved.get(v, 0.0) + float(np.linalg.norm(new - co[v])); me.vertices[v].co = tuple(new)
print(f'DESPIKE unfold: {it} relax rounds, folded vertices left {len(folded())}')
import json
json.dump({'moved': sorted(int(v) for v in moved)},
          open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'despike_moved.json'), 'w'))
for v, d in sorted(moved.items(), key=lambda x: -x[1]):
    print(f'DESPIKE vertex {v} piece {pv[v]} moved {d * 100:.1f} cm')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[1]))
