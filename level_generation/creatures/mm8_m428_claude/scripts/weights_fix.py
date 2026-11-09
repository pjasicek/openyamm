"""Component ownership for the female dark elf (work/rig_v1.blend -> work/rig_owned.blend), starting from Meshy's
auto-rig weights (build_rig.py transferred them by name).

Pieces (step1_clean.py): 0 one shell for head skin, neck, bodice, sleeves and the whole dress; 1 hidden legs and
shoes; 2 hair; 3/4 left/right forearm + hand; 5 fringe; 8/9 eyes; 17/18 mouth; 10/11 shoulder bands; lacing,
belt and buckle pieces 6, 7, 12-16, 19-22.
- head parts (5, 8, 9, 17, 18) rigid on B_Head;
- hair: B_Head above the shoulders, blending into B_Spine2 down the back (the long hair hangs from the shoulder
  blades; a head turn bends it at the shoulders instead of swinging it through the back);
- hands: arm bones only (fingers come later from finger_weights.py);
- legs/shoes: leg bones only;
- piece 0 above the waist: torso, neck, head, clavicle and arm bones; upper-arm/forearm weight fades out medially
  (chest and back carry none) and leg weight is moved to the pelvis; the skirt below the waist is re-weighted by
  dress_rig.py;
- lacing, belt, buckle and shoulder bands copy the weights of the nearest 8 piece-0 vertices."""
import bpy
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/rig_v1.blend'))
body = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = body.data
co = np.array([tuple(v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight


def keep(ids, allowed, fallback):
    cols = [gi[n] for n in allowed]
    row = W[ids].copy(); row[:, [j for j in range(len(names)) if j not in cols]] = 0
    bad = row.sum(1) < 1e-6; row[bad, gi[fallback]] = 1
    W[ids] = row / row.sum(1, keepdims=True)


def rigid(pieces, bone):
    ids = np.flatnonzero(np.isin(pv, pieces)); W[ids] = 0; W[ids, gi[bone]] = 1


rigid([5, 8, 9, 17, 18], 'B_Head')
ids = np.flatnonzero(pv == 2)
z0, z1 = 1.30, 1.44
h = np.clip((co[ids, 2] - z0) / (z1 - z0), 0, 1)
W[ids] = 0; W[ids, gi['B_Head']] = h; W[ids, gi['B_Spine2']] = 1 - h
for side, piece in (('L', 3), ('R', 4)):
    keep(np.flatnonzero(pv == piece), [f'B_{side}_{x}' for x in ('Forearm', 'Hand', 'UpperArm')], f'B_{side}_Hand')
legs = ['B_Pelvis'] + [f'B_{s}_{x}' for s in 'LR' for x in ('Thigh', 'Calf', 'Foot', 'Toe0')]
keep(np.flatnonzero(pv == 1), legs, 'B_Pelvis')
WAIST = 1.04
top = np.flatnonzero((pv == 0) & (co[:, 2] >= WAIST - 0.06))
for s in 'LR':                                      # leg weight on the bodice/hips goes to the pelvis
    for x in ('Thigh', 'Calf', 'Foot', 'Toe0'):
        W[top, gi['B_Pelvis']] += W[top, gi[f'B_{s}_{x}']]; W[top, gi[f'B_{s}_{x}']] = 0
sh_x = abs(rig.data.bones['B_L_UpperArm'].head_local.x)
fade = np.clip((np.abs(co[top, 0]) - (sh_x - 0.06)) / 0.05, 0, 1)
for s in 'LR':
    for x in ('UpperArm', 'Forearm', 'Hand'):
        moved = W[top, gi[f'B_{s}_{x}']] * (1 - fade)
        W[top, gi[f'B_{s}_{x}']] -= moved
        W[top, gi[f'B_{s}_Clavicle']] += moved
keep(top, ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head'] +
     [f'B_{s}_{x}' for s in 'LR' for x in ('Clavicle', 'UpperArm', 'Forearm', 'Hand')], 'B_Spine2')
p0 = np.flatnonzero(pv == 0)
for piece in (6, 7, 10, 11, 12, 13, 14, 15, 16, 19, 20, 21, 22):
    for i in np.flatnonzero(pv == piece):
        near = p0[np.argsort(np.linalg.norm(co[p0] - co[i], axis=1))[:8]]
        W[i] = W[near].mean(0)
W /= W.sum(1, keepdims=True)
assert np.isfinite(W).all()
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for n in names:
    body.vertex_groups.new(name=n)
for i, row in enumerate(W):
    for j in np.flatnonzero(row > 1e-5):
        body.vertex_groups[int(j)].add([i], float(row[j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/rig_owned.blend'))
print('RULE component ownership', {int(p): int((pv == p).sum()) for p in np.unique(pv)})
