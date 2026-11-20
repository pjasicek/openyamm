"""G4 weight rules (measured faults: armlets 9x, chest armour 6.6x, shoulder skin 5x stretch in the attack).
1. Every shell except the skin (piece 0) and the hair (1) copies the weights of the nearest skin vertices (inverse
   distance over the 4 nearest), so armour follows the body under it instead of Meshy's own guesses.
2. Torso armour (shell centroid within the ribcage box) drops upper-arm/forearm/hand weight, renormalised.
3. (dropped) small limb rings rigid on their dominant bone - see the note in the loop.
4. Skin: upper-arm weight fades out medially across the shoulder - full at the shoulder joint, zero 7 cm toward the
   midline (measured along the clavicle direction) - and the removed weight goes to the clavicle.
Each rule reports what it changed. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
tris = {p: 0 for p in np.unique(pv)}
for poly in me.polygons:
    tris[int(pv[poly.vertices[0]])] += len(poly.vertices) - 2
ARM = [gi[n] for n in names if any(k in n for k in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]   # incl. twist bones
skin = np.where(pv == 0)[0]
kd = KDTree(len(skin))
for i, s in enumerate(skin):
    kd.insert(co[s], i)
kd.balance()
J = lambda n: np.array(rig.data.bones[n].head_local)
chest_lo, chest_hi = J('B_Spine1')[2] - 0.05, J('B_Neck')[2] + 0.02
half = abs(J('B_L_UpperArm')[0]) - 0.02
for p in sorted(tris):
    if p in (0, 1):
        continue
    ids = np.where(pv == p)[0]
    new = np.zeros((len(ids), len(names)))
    gaps = []
    for k, i in enumerate(ids):
        hits = kd.find_n(co[i], 4)
        gaps.append(hits[0][2])
        w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
        new[k] = (w[:, None] * Wt[[skin[h[1]] for h in hits]]).sum(0) / w.sum()
    c = co[ids].mean(0)
    gap = float(np.median(gaps))
    if gap > 0.015:
        # no skin directly under this shell (e.g. the leggings ARE the legs' surface): keep its own weights
        print('RULE piece', p, tris[p], 'tris: kept own weights (median skin gap', round(gap * 100, 1), 'cm)')
        continue
    rule = f'skin-copy (gap {gap * 100:.1f} cm)'
    if chest_lo < c[2] < chest_hi and abs(c[0]) < half:
        new[:, ARM] = 0; rule = 'torso armour (arm weight dropped)'
    elif tris[p] <= 400:
        # small rigid rings (armlets): rigid on the bone that dominates the skin under them (>= 80 %); twist ramps
        # are placed so that no ring sits over a transition (twist_bones.py), otherwise copy the skin
        share = new.sum(0) / max(new.sum(), 1e-9); dom = int(np.argmax(share))
        if share[dom] >= 0.8:
            new[:] = 0; new[:, dom] = 1; rule = f'rigid on {names[dom]} (skin share {share[dom]:.2f})'
    new /= np.maximum(new.sum(1, keepdims=True), 1e-9)
    Wt[ids] = new
    if p in (5, 10, 12) or tris[p] > 400:
        print('RULE piece', p, tris[p], 'tris:', rule)
# 4. shoulder fade on the skin
moved = 0
for s in ('L', 'R'):
    sh, cl = J(f'B_{s}_UpperArm'), J(f'B_{s}_Clavicle')
    d = (sh - cl) / np.linalg.norm(sh - cl)                       # clavicle direction, pointing out to the shoulder
    ua, cv = gi[f'B_{s}_UpperArm'], gi[f'B_{s}_Clavicle']
    for i in skin:
        m = (co[i] - sh) @ d                                        # > 0 outside the joint, < 0 toward the midline
        if m < 0 and Wt[i, ua] > 0:
            keep = max(0.0, 1.0 + m / 0.07)
            dw = Wt[i, ua] * (1 - keep)
            Wt[i, ua] -= dw; Wt[i, cv] += dw; moved += dw > 1e-3
print('RULE shoulder fade: skin vertices changed', moved)
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(Wt[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(Wt[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
