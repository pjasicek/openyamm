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
# reference surface: the skin and the two foot shells (the goblin's lower legs and feet ARE those shells; the ankle
# straps and greaves sit on them, 20-26 cm from the nearest piece-0 skin)
SURFACE = (0, 1, 2)
skin = np.where(np.isin(pv, SURFACE))[0]
kd = KDTree(len(skin))
for i, s in enumerate(skin):
    kd.insert(co[s], i)
kd.balance()
J = lambda n: np.array(rig.data.bones[n].head_local)
# goblin shells: the skirt strips (small pieces hanging below the belt) blend from the pelvis at the belt to the skin
# under them at the hem, so they stay on the belt and follow the thighs; the pouch hangs on the belt (rigid pelvis);
# small attachments (spikes, studs) ride the plate they sit on (nearest larger shell within 1.5 cm)
PEL = gi['B_Pelvis']
cz = {p: co[pv == p][:, 2] for p in tris}
STRIPS = {p for p in tris if p not in SURFACE and tris[p] < 100 and 0.55 < cz[p].min() < 0.7 and cz[p].max() > 0.85}
HOSTS = [p for p in tris if p not in SURFACE and tris[p] > 100]
host_kd = {}
for h in HOSTS:
    hid = np.where(pv == h)[0]; k_ = KDTree(len(hid))
    for i, x in enumerate(hid):
        k_.insert(co[x], i)
    k_.balance(); host_kd[h] = (hid, k_)
print('RULE skirt strips', sorted(STRIPS))
chest_lo, chest_hi = J('B_Spine1')[2] - 0.05, J('B_Neck')[2] + 0.02
half = abs(J('B_L_UpperArm')[0]) - 0.02
for p in sorted(tris):
    if p in SURFACE:
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
    # goblin armour stands 1.6-2.5 cm off the skin and the skirt strips hang 2-6 cm off the thighs (bar1: 1.5 cm)
    if gap > float(os.environ.get('SKIN_GAP', '0.07')):
        # no skin directly under this shell (e.g. the leggings ARE the legs' surface): keep its own weights
        print('RULE piece', p, tris[p], 'tris: kept own weights (median skin gap', round(gap * 100, 1), 'cm)')
        continue
    rule = f'skin-copy (gap {gap * 100:.1f} cm)'
    if p == 4:
        new[:] = 0; new[:, PEL] = 1; rule = 'pouch rigid on the pelvis (hangs on the belt)'
        Wt[ids] = new; print('RULE piece', p, tris[p], 'tris:', rule); continue
    if p in STRIPS:
        # pelvis at the belt -> the thighs at the hem with ONE left/right mixture per strip (by its centre x): the skin
        # copy split the middle strips across their width (left half on the left thigh, right half on the right one),
        # which stretched them 8.9x between the legs in the wide cast stance (gob2 review 1); a partial thigh share
        # fixed that but let the thighs poke 5 cm through the strips, so the hem follows the legs fully
        z = co[ids][:, 2]; top, bot = z.max(), z.min()
        a = np.clip((top - z) / max(top - bot, 1e-3), 0, 1)[:, None]          # 0 at the belt, 1 at the hem
        xc = float(co[ids][:, 0].mean())
        wl = float(np.clip(0.5 + xc / 0.12, 0, 1))
        new = np.zeros_like(new); new[:, PEL] = 1 - a[:, 0]
        new[:, gi['B_L_Thigh']] = a[:, 0] * wl; new[:, gi['B_R_Thigh']] = a[:, 0] * (1 - wl)
        Wt[ids] = new / np.maximum(new.sum(1, keepdims=True), 1e-9)
        print('RULE piece', p, tris[p], f'tris: skirt strip (pelvis -> thighs L {wl:.2f} / R {1 - wl:.2f} at the hem, x {xc:+.3f})'); continue
    if tris[p] <= 50 and p not in STRIPS:
        best = None
        for h, (hid, k_) in host_kd.items():
            if h == p:
                continue
            dmin = float(np.median([k_.find(co[i])[2] for i in ids]))   # median: a min picked the gorget for a pauldron spike
            if best is None or dmin < best[1]:
                best = (h, dmin)
        if best is not None and best[1] < 0.015:
            hid, k_ = host_kd[best[0]]
            Wt[ids] = np.array([Wt[hid[k_.find(co[i])[1]]] for i in ids])
            print('RULE piece', p, tris[p], f'tris: attachment, copies host piece {best[0]} ({best[1] * 100:.1f} cm)'); continue
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
    print('RULE piece', p, tris[p], 'tris:', rule)
# 4. shoulder fade on the skin
moved = 0
skin = np.where(pv == 0)[0]
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
# 5. jaw free of the shoulders (gob2 review 2): Meshy weighted even the jaw underside 21-37 % to the clavicles/upper
#    arms, so a shrug dragged the jaw down onto the shoulder. Skin above the jaw line (B_Head joint - 2 cm, ramp over
#    3 cm below it) inside the neck's width loses that weight to the neck/head; the side of the neck below keeps it and
#    still lifts with a shrug (a first version cleaned the whole neck above the clavicles: the jaw then stayed put and
#    the shoulder met it 5 cm deep instead of 2 cm).
jz = J('B_Head')[2] - 0.02; nz = J('B_Neck')[2]; ax_x = J('B_Neck')[0]
SH = [gi[n] for n in names if any(f'B_{s_}_{b}' == n for s_ in 'LR' for b in ('Clavicle', 'UpperArm', 'UpperArmTwist'))]
neck_moved = 0
for i in skin:
    fz = float(np.clip((co[i, 2] - (jz - 0.03)) / 0.03, 0, 1))
    if fz <= 0:
        continue
    keep_lat = float(np.clip((abs(co[i, 0] - ax_x) - 0.07) / 0.07, 0, 1))
    r = fz * (1 - keep_lat)
    dw = Wt[i, SH].sum() * r
    if dw > 1e-4:
        Wt[i, SH] *= (1 - r)
        Wt[i, gi['B_Head'] if co[i, 2] > jz else gi['B_Neck']] += dw; neck_moved += 1
print('RULE jaw free of the shoulders: skin vertices changed', neck_moved)
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(Wt[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(Wt[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
