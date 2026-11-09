"""v2a fix (user review 2026-10-21) on the rigged, reduced mesh; topology and UVs stay:
1. ABS: the Smart Topology torso has a faceted ledge under the pecs and at the flanks above the belt (in Meshy's own
   mesh, sharpened by the reduction); the Orc Idle's spine flexion folds it into a protruding corner. Taubin smoothing
   (lambda 0.5 / mu -0.53, ABS_ITER passes) of the body skin (garment 0) in front of the torso between the pec line and
   the belt (rest z 1.00-1.34, y < 0.02, |x| < 0.33, arm weight < 0.3), eased in over 4 cm at the region borders.
2. SHOULDERS: the upper-arm weight fell from 1 to 0 over a narrow band across the back of the deltoid, which creased
   when the arm is out, and the deltoid's lower/back border is a jagged ledge in Meshy's mesh. Taubin smoothing
   (SHG_ITER passes) of the skin within 0.24 m of each shoulder joint (eased from 0.16 m, jaw/neck excluded), and
   Laplacian smoothing (SH_ITER passes) of the clavicle / upper arm / upper-arm twist / spine2 / neck weights within
   0.26 m (eased from 0.16 m); other groups kept, rows renormalised. Both sides are treated identically.
Marks the mesh ('v2a_smooth_fixed') so it is applied once. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
if me.get('v2a_smooth_fixed'):
    raise SystemExit('SMOOTHFIX already applied to this mesh')
ABS_ITER = int(os.environ.get('ABS_ITER', '12')); SH_ITER = int(os.environ.get('SH_ITER', '12'))
SHG_ITER = int(os.environ.get('SHG_ITER', '8'))
n = len(me.vertices)
co = np.array([tuple(v.co) for v in me.vertices])
gv = np.zeros(n, np.int32); me.attributes['garment'].data.foreach_get('value', gv)
E = np.array([tuple(e.vertices) for e in me.edges])
skin = gv == 0
names = [g.name for g in body.vertex_groups]; gi = {nm: i for i, nm in enumerate(names)}
W = np.zeros((n, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
arm = W[:, [i for i, nm in enumerate(names) if any(k in nm for k in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]].sum(1)
sm = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))


def umbrella(P, mask):
    """Mean of each masked vertex's skin neighbours minus itself (zero elsewhere)."""
    acc = np.zeros_like(P); deg = np.zeros(len(P))
    ee = E[skin[E[:, 0]] & skin[E[:, 1]]]
    np.add.at(acc, ee[:, 0], P[ee[:, 1]]); np.add.at(acc, ee[:, 1], P[ee[:, 0]])
    np.add.at(deg, ee[:, 0], 1); np.add.at(deg, ee[:, 1], 1)
    L = np.where(deg[:, None] > 0, acc / np.maximum(deg, 1)[:, None] - P, 0)
    L[~mask] = 0
    return L


# ---------------------------------------------------------------- 1. abs
x, y, z = co[:, 0], co[:, 1], co[:, 2]
f = (sm((z - 1.00) / 0.04) * sm((1.34 - z) / 0.04) * sm((0.02 - y) / 0.04) * sm((0.33 - np.abs(x)) / 0.04)
     * sm((0.3 - arm) / 0.15))
f[~skin] = 0
mask = f > 0
P = co.copy()
for _ in range(ABS_ITER):
    P += 0.5 * umbrella(P, mask) * f[:, None]
    P += -0.53 * umbrella(P, mask) * f[:, None]
# shoulders: the deltoid's back/lower border is a jagged ledge in Meshy's mesh (a corner in the arm's back contour)
fs = np.zeros(n)
for s_ in 'LR':
    sh = np.array(rig.data.bones[f'B_{s_}_UpperArm'].head_local)
    fs = np.maximum(fs, sm((0.24 - np.linalg.norm(co - sh, axis=1)) / 0.08))
fs[~skin] = 0
fs *= sm((1.0 - W[:, gi['B_Head']] - W[:, gi['B_Neck']]) / 0.5)       # leave the jaw and neck alone
smask = fs > 0
for _ in range(SHG_ITER):
    P += 0.5 * umbrella(P, smask) * fs[:, None]
    P += -0.53 * umbrella(P, smask) * fs[:, None]
ms = np.linalg.norm(P - co, axis=1)
print('SMOOTHFIX shoulder geometry: vertices', int(smask.sum()), 'moved mm p50/max',
      round(float(np.median(ms[smask & ~mask])) * 1000, 1), round(float(ms[smask].max()) * 1000, 1))
move = np.linalg.norm(P - co, axis=1)
print('SMOOTHFIX abs: vertices', int(mask.sum()), 'moved mm p50/max', round(float(np.median(move[mask])) * 1000, 1),
      round(float(move.max()) * 1000, 1))
for v, p in zip(me.vertices, P):
    v.co = p
# ---------------------------------------------------------------- 2. shoulder weights
G = [gi[nm] for nm in names if any(nm == f'B_{s}_{b}' or nm.startswith(f'B_{s}_{b}') for s in 'LR'
                                    for b in ('Clavicle', 'UpperArm')) or nm in ('B_Spine2', 'B_Neck')]
G = [g for g in G if 'Forearm' not in names[g]]
ws = np.zeros(n)
for s in 'LR':
    sh = np.array(rig.data.bones[f'B_{s}_UpperArm'].head_local)
    d = np.linalg.norm(co - sh, axis=1)
    ws = np.maximum(ws, sm((0.26 - d) / 0.10))
ws[~skin] = 0
Wn = W.copy()
ee = E[skin[E[:, 0]] & skin[E[:, 1]]]
for _ in range(SH_ITER):
    acc = np.zeros((n, len(G))); deg = np.zeros(n)
    np.add.at(acc, ee[:, 0], Wn[ee[:, 1]][:, G]); np.add.at(acc, ee[:, 1], Wn[ee[:, 0]][:, G])
    np.add.at(deg, ee[:, 0], 1); np.add.at(deg, ee[:, 1], 1)
    mean = acc / np.maximum(deg, 1)[:, None]
    tot = Wn[:, G].sum(1, keepdims=True)                         # keep the shoulder groups' share of each row
    new = Wn[:, G] + 0.5 * (mean - Wn[:, G]) * ws[:, None]
    new *= tot / np.maximum(new.sum(1, keepdims=True), 1e-9)
    Wn[:, G] = np.where(tot > 0, new, Wn[:, G])
Wn /= np.maximum(Wn.sum(1, keepdims=True), 1e-9)
ch = np.abs(Wn - W).sum(1)
print('SMOOTHFIX shoulder weights: vertices in reach', int((ws > 0).sum()), 'changed > 0.05:', int((ch > 0.05).sum()),
      'max change', round(float(ch.max()), 3))
for g in G:
    vg = body.vertex_groups[g]
    for i in np.where(ws > 0)[0]:
        if Wn[i, g] > 1e-4:
            vg.add([int(i)], float(Wn[i, g]), 'REPLACE')
        elif W[i, g] > 0:
            vg.remove([int(i)])
me['v2a_smooth_fixed'] = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
