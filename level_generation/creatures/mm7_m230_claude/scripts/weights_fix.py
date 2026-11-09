"""m230 weight rules (plate armour: separate segments, no skin under them), by garment (scripts/garments.py):
0 armour     Meshy weights per vertex, then each segment is made RIGID on its dominant bone when that bone holds
             >= RIGID_SHARE of the segment's summed weight (plates do not bend; joints are covered by the overlap of
             neighbouring segments). Segments without a dominant bone (cuirass, thigh plates, gauntlets) keep Meshy's
             weights plus the shoulder fade (upper arm -> clavicle over 7 cm medially) and no arm weight on the cuirass
             front/back below the armpits. The gauntlets keep Meshy's hand weights; fingers come from finger_weights.py.
1 head       great helm, eagle crest, plume: rigid on B_Head.
2 skirts     tabard skirts (front/back): B_Pelvis at the belt -> the thighs at the hem, the left/right mix per vertex
             by its x (a panel spans both legs).
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
RIGID_SHARE = float(os.environ.get('RIGID_SHARE', '0.8'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
gv = np.zeros(nv, np.int32); me.attributes['garment'].data.foreach_get('value', gv)
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
J = lambda n: np.array(rig.data.bones[n].head_local)
idx = lambda keys: [gi[n] for n in names if any(k in n for k in keys)]
ARMS = idx(('UpperArm', 'Forearm', 'Hand', 'Finger'))
PEL = gi['B_Pelvis']
HAND = {3, 4}
# shoulder fade on the armour (as the skin rule)
moved = 0
arm_mask = gv == 0
for s in ('L', 'R'):
    sh, cl = J(f'B_{s}_UpperArm'), J(f'B_{s}_Clavicle')
    d = (sh - cl) / np.linalg.norm(sh - cl)
    ua, cv = gi[f'B_{s}_UpperArm'], gi[f'B_{s}_Clavicle']
    for i in np.where(arm_mask)[0]:
        m = (co[i] - sh) @ d
        if m < 0 and Wt[i, ua] > 0:
            keep = max(0.0, 1.0 + m / 0.07)
            dw = Wt[i, ua] * (1 - keep)
            Wt[i, ua] -= dw; Wt[i, cv] += dw; moved += dw > 1e-3
print('RULE armour shoulder fade: vertices changed', moved)
count = {}
for p in sorted(set(pv.tolist())):
    ids = np.where(pv == p)[0]; g = int(gv[ids[0]])
    if g == 1:
        new = np.zeros((len(ids), len(names))); new[:, gi['B_Head']] = 1; rule = 'head'
    elif g == 2:
        z = co[ids][:, 2]; top, bot = z.max(), z.min()
        a = np.clip((top - 0.03 - z) / max(top - 0.03 - bot, 1e-3), 0, 1)
        wl = np.clip(0.5 + co[ids][:, 0] / 0.12, 0, 1)
        new = np.zeros((len(ids), len(names))); new[:, PEL] = 1 - a
        new[:, gi['B_L_Thigh']] = a * wl; new[:, gi['B_R_Thigh']] = a * (1 - wl); rule = 'skirt strip'
    else:
        share = Wt[ids].sum(0) / max(Wt[ids].sum(), 1e-9); dom = int(np.argmax(share))
        if p not in HAND and share[dom] >= RIGID_SHARE:
            new = np.zeros((len(ids), len(names))); new[:, dom] = 1; rule = f'rigid {names[dom]} ({share[dom]:.2f})'
        else:
            new = Wt[ids].copy(); rule = f'Meshy (top {names[dom]} {share[dom]:.2f})'
            # cuirass/tabard top: no arm weight on the torso below the armpit band
            if names[dom].startswith('B_Spine'):
                low = co[ids][:, 2] < J('B_Spine2')[2]
                new[np.ix_(low, ARMS)] = 0
    Wt[ids] = new / np.maximum(new.sum(1, keepdims=True), 1e-9)
    count[rule.split(' (')[0].split(' B_')[0]] = count.get(rule.split(' (')[0].split(' B_')[0], 0) + 1
    print('RULE piece', p, len(ids), 'verts:', rule)
print('RULE summary', count)
# arm plates: smooth the weights inside each arm segment over its own edges (ARM_SMOOTH passes), so an elbow bend
# spreads along the plate instead of tearing a narrow band (G4 2026-10-20: death p99 2.48, max 4.17 at the left elbow)
edges = np.array([tuple(e.vertices) for e in me.edges])
armw = Wt[:, ARMS].sum(1)
smooth_p = [p for p in set(pv.tolist()) if gv[pv == p][0] == 0 and p not in HAND and armw[pv == p].mean() > 0.5]
sm = np.isin(pv, smooth_p)
E = edges[sm[edges[:, 0]] & sm[edges[:, 1]] & (pv[edges[:, 0]] == pv[edges[:, 1]])]
for _ in range(int(os.environ.get('ARM_SMOOTH', '8'))):
    acc = Wt.copy(); deg = np.ones(nv)
    np.add.at(acc, E[:, 0], Wt[E[:, 1]]); np.add.at(acc, E[:, 1], Wt[E[:, 0]])
    np.add.at(deg, E[:, 0], 1); np.add.at(deg, E[:, 1], 1)
    Wt[sm] = (acc / deg[:, None])[sm]
print('RULE arm plates smoothed', sorted(smooth_p))
for g in body.vertex_groups:
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i in range(nv):
    for j in np.nonzero(Wt[i] > 1e-4)[0]:
        body.vertex_groups[j].add([i], float(Wt[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
