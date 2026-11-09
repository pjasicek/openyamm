"""hkr Trooper caste bulk (2026-10-22, user: the Trooper read as a thin Demon; the concept trooper is bulky): the rest
mesh of the Body inflated along its normals by a per-bone amount blended with the skin's own weights (weights, joints
and clips unchanged), the offsets smoothed over the mesh (Laplacian, SMOOTH passes) so no seam shows at bone borders:
upper chest and clavicles (broad shoulders, barrel chest), neck base, upper arms and forearms a little (fading to the
wrist; 35 % on their body-facing side), thighs, calves (fading to the ankle); head, hands, feet and tail untouched. Loose pieces (spikes, chest
ornament, teeth) move with the mean offset of their nearest main-skin vertices, so they stay attached. The thin rest
positions are kept in the vertex attribute `thin_co` (export_hkr.py MODE=base restores them: the bare Kreegan stays
thin for the Drudges). Idempotent: an existing `thin_co` is the starting shape. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
SCALE, SMOOTH = float(os.environ.get('BULK', '1.0')), int(os.environ.get('SMOOTH', '12'))
# metres along the normal per bone (left and right alike)
AMOUNT = {'B_Spine2': 0.024, 'B_Spine1': 0.020, 'B_Spine': 0.012, 'B_Pelvis': 0.016, 'B_Neck': 0.012,
          'Clavicle': 0.022, 'UpperArm': 0.026, 'UpperArmTwist': 0.026, 'Forearm': 0.014, 'ForearmTwist': 0.012,
          'Thigh': 0.032, 'Calf': 0.020}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
nv = len(me.vertices)
if 'thin_co' in me.attributes:
    thin = np.zeros(nv * 3); me.attributes['thin_co'].data.foreach_get('vector', thin); thin = thin.reshape(-1, 3)
    me.vertices.foreach_set('co', thin.ravel()); me.update()
else:
    thin = np.array([v.co[:] for v in me.vertices])
    at = me.attributes.new('thin_co', 'FLOAT_VECTOR', 'POINT'); at.data.foreach_set('vector', thin.ravel())
names = [g.name for g in body.vertex_groups]; W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
amt = np.zeros(len(names))
for i, n in enumerate(names):
    key = n if n in AMOUNT else (n.split('_', 2)[2] if n.startswith(('B_L_', 'B_R_')) else None)
    amt[i] = AMOUNT.get(key, 0.0) if key else 0.0
J = lambda n: np.array(rig.data.bones[n].head_local)
F = np.ones((nv, len(names)))                             # per-vertex share of each bone's amount
for s_ in 'LR':                                            # forearm toward the wrist, calf toward the ankle
    for upper, lower, keep in ((f'B_{s_}_Forearm', f'B_{s_}_Hand', 0.25), (f'B_{s_}_Calf', f'B_{s_}_Foot', 0.3)):
        h, t = J(upper), J(lower); ax = t - h; L = np.linalg.norm(ax); ax /= L
        fr = np.clip(((thin - h) @ ax) / L, 0, 1)
        for c in [i for i, n in enumerate(names) if n.startswith(upper)]:
            F[:, c] = 1 - (1 - keep) * fr
if 'B_Neck' in names:                                      # the neck only at its base
    F[:, names.index('B_Neck')] = 1 - np.clip((thin[:, 2] - J('B_Neck')[2]) / 0.06, 0, 1)
NRM0 = np.array([v.normal[:] for v in me.vertices])
for c in [i for i, n in enumerate(names) if any(t in n for t in ('UpperArm', 'Forearm'))]:
    # the arms bulk outward (deltoid, biceps), little on their body-facing side: the supporting arm crosses the cuirass
    side = np.sign(thin[:, 0]); out = np.clip(NRM0[:, 0] * side, -1, 1)          # +1 facing away from the midline
    F[:, c] *= 0.35 + 0.65 * np.clip(0.5 + 0.5 * out, 0, 1)
off = (W * F) @ amt * SCALE
PIECE = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', PIECE)
main = PIECE == 0
nb = [[] for _ in range(nv)]
for e in me.edges:
    i, j = e.vertices; nb[i].append(j); nb[j].append(i)
for it in range(SMOOTH):                                   # Laplacian on the offsets over the main skin
    new = off.copy()
    for i in np.nonzero(main)[0]:
        if nb[i]: new[i] = 0.5 * off[i] + 0.5 * np.mean(off[nb[i]])
    off = new
NRM = np.array([v.normal[:] for v in me.vertices])
D = NRM * off[:, None]
kd = KDTree(int(main.sum()))
mi = np.nonzero(main)[0]
for k, i in enumerate(mi): kd.insert(Vector(thin[i]), k)
kd.balance()
for pc in sorted(set(PIECE.tolist()) - {0}):              # loose pieces ride their nearest skin
    sel = np.nonzero(PIECE == pc)[0]
    near = [mi[k] for c in thin[sel] for (_, k, _) in kd.find_n(Vector(c), 3)]
    D[sel] = D[near].mean(0)
me.vertices.foreach_set('co', (thin + D).ravel()); me.update()
rep = {'max_cm': round(float(np.abs(off).max() * 100), 2), 'mean_cm_moved': round(float(off[off > 1e-4].mean() * 100), 2),
       'verts_moved': int((np.linalg.norm(D, axis=1) > 1e-4).sum())}
print('BULK', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[1]))
