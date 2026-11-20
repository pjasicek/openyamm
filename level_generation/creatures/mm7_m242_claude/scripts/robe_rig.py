"""Robe chains and cloth weights for the legless ghost (after build_rig.py, which left every cloth piece on its nearest
bone). Below the pelvis the robe hangs empty, so it gets its own soft chains:
- bones Robe_<col><layer>_<i>: columns L/C/R at x = +COL_X / 0 / -COL_X, layers F (front, y = Y_F) and B (back,
  y = Y_B), NSEG connected segments from the pelvis height down to HEM_Z; parent B_Pelvis; 24 bones.
- every cloth vertex (attribute 'cloth' = 1: the hood/cape shell P01 and the robe shreds):
  body share b = smoothstep((z - CHAIN_TOP) / BLEND_Z): above the pelvis band the cloth rides the body:
    the hood (z above the neck joint - 2 cm, inside 0.2 m of the head axis) -> B_Head, fading to B_Neck at its base;
    elsewhere the spine bones by height (linear between B_Spine..B_Spine2 heads), plus a sleeve share on the upper arm
    for cape vertices within SLEEVE_R of the humerus (beyond the shoulder joint), up to SLEEVE_MAX, so a raised arm
    lifts the cape draped over it instead of piercing it;
  chain share (1 - b): column mix by x and layer mix by y, CONSTANT per shred (its centroid; the cape shell uses its
  vertex), and the segment by height (linear between the chain joints), so a strip bends but never tears.
- bone pieces keep build_rig.py's rigid weights.
At rest every chain carries its vertices exactly (rest pose), so the shape is unchanged until the clips move them.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
COL_X, Y_F, Y_B, NSEG, HEM_Z = E('COL_X', 0.22), E('Y_F', -0.07), E('Y_B', 0.08), int(E('NSEG', 4)), E('HEM_Z', 0.10)
CHAIN_TOP, BLEND_Z, SLEEVE_R, SLEEVE_MAX = E('CHAIN_TOP', 1.10), E('BLEND_Z', 0.22), E('SLEEVE_R', 0.11), E('SLEEVE_MAX', 0.6)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
H = lambda n: np.array(rig.data.bones[n].head_local)
pel = H('B_Pelvis')
top = pel[2]
zs = np.linspace(top, HEM_Z, NSEG + 1)
COLS = {'L': COL_X, 'C': 0.0, 'R': -COL_X}; LAY = {'F': Y_F, 'B': Y_B}
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for c, x in ({} if 'Robe_LF_1' in eb else COLS).items():           # re-run on a rigged master: keep its chains
    for l, y in LAY.items():
        parent = eb['B_Pelvis']
        for i in range(NSEG):
            b = eb.new(f'Robe_{c}{l}_{i + 1}')
            b.head = Vector((pel[0] + x, pel[1] + y, zs[i])); b.tail = Vector((pel[0] + x, pel[1] + y, zs[i + 1]))
            b.align_roll(Vector((0, -1, 0))); b.parent = parent; b.use_connect = i > 0; b.use_deform = True
            parent = b
bpy.ops.object.mode_set(mode='OBJECT')
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
cl = np.zeros(nv, np.int32); me.attributes['cloth'].data.foreach_get('value', cl)
for c in COLS:
    for l in LAY:
        for i in range(NSEG):
            if f'Robe_{c}{l}_{i + 1}' not in body.vertex_groups:
                body.vertex_groups.new(name=f'Robe_{c}{l}_{i + 1}')
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}


def ss(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


def seg_t(p, a, b):
    d = b - a; t = np.clip(((p - a) @ d) / (d @ d), 0, 1)
    return t, np.linalg.norm(p - (a + np.outer(t, d)), axis=1)


SP = [('B_Pelvis', H('B_Pelvis')[2]), ('B_Spine', H('B_Spine')[2]), ('B_Spine1', H('B_Spine1')[2]), ('B_Spine2', H('B_Spine2')[2])]
neck_z, head_z = H('B_Neck')[2], H('B_Head')[2]
ids = np.where(cl == 1)[0]
W = np.zeros((len(ids), len(names)))
P = co[ids]
b = ss((P[:, 2] - CHAIN_TOP) / BLEND_Z)
# ---- body share
hax = np.array([H('B_Head')[0], H('B_Head')[1]])
# the hood/cowl: from HOOD_LOW below the neck joint, within HOOD_R of the head axis; its head share ramps over
# HOOD_RAMP (user review 2026-10-20: an 8 cm ramp smeared the cowl into a sheet when the head bent forward), the rest
# on the neck above the collar and on B_Spine2 below it
HOOD_LOW, HOOD_R, HOOD_RAMP = E('HOOD_LOW', 0.10), E('HOOD_R', 0.22), E('HOOD_RAMP', 0.18)
# ... and everything of the shell above the head joint: the hood's pointed peak reaches 23 cm behind the head axis,
# was left on the spine and smeared 9.6x when the head bent (the user's 'spike' on the back of the hood)
hood = ((P[:, 2] > neck_z - HOOD_LOW) & (np.hypot(P[:, 0] - hax[0], P[:, 1] - hax[1]) < HOOD_R)) | (P[:, 2] > head_z - 0.02)
hw = ss((P[:, 2] - (neck_z - HOOD_LOW)) / HOOD_RAMP)
nf = ss((P[:, 2] - (neck_z - HOOD_LOW)) / 0.08)
zz = [z for _, z in SP]
for k in range(len(ids)):
    if hood[k]:
        W[k, gi['B_Head']] += b[k] * hw[k]
        W[k, gi['B_Neck']] += b[k] * (1 - hw[k]) * nf[k]; W[k, gi['B_Spine2']] += b[k] * (1 - hw[k]) * (1 - nf[k]); continue
    z = P[k, 2]
    if z >= zz[-1]:
        W[k, gi['B_Spine2']] += b[k]
    else:
        j = max(0, np.searchsorted(zz, z) - 1); f = np.clip((z - zz[j]) / (zz[j + 1] - zz[j]), 0, 1)
        W[k, gi[SP[j][0]]] += b[k] * (1 - f); W[k, gi[SP[j + 1][0]]] += b[k] * f
# sleeve share on the upper arm (cape over the humerus)
for s, sg in (('L', 1.0), ('R', -1.0)):
    sh, el = H(f'B_{s}_UpperArm'), H(f'B_{s}_Forearm')
    t, d = seg_t(P, sh, el)
    # only the cape shell P01 drapes over the humerus; the small shreds beside it flipped up into spikes when the arm
    # rose (attack raise)
    on = (sg * P[:, 0] > sg * sh[0] - 0.04) & ~hood & (pv[ids] == 1)
    share = SLEEVE_MAX * ss(1 - d / SLEEVE_R) * ss((t - 0.05) / 0.3) * on       # nothing on the collar
    moved = W[:, :] * share[:, None]
    W -= moved; W[:, gi[f'B_{s}_UpperArm']] += moved.sum(1)
# ---- chain share
piece_c = {p: co[pv == p].mean(0) for p in set(pv[ids].tolist())}
for k, vi in enumerate(ids):
    ch = 1 - b[k]
    if ch <= 1e-4:
        continue
    ref = co[vi] if pv[vi] == 1 else piece_c[pv[vi]]
    x = np.clip((ref[0] - pel[0]) / COL_X, -1, 1)
    cw = {'L': max(x, 0), 'C': 1 - abs(x), 'R': max(-x, 0)}
    # front or back layer, nearly a step (a column x layer x segment blend would need 8 influences; the export keeps 4)
    yl = float(ss((ref[1] - pel[1] - (Y_F + Y_B) / 2) / 0.04 + 0.5))
    lw = {'F': 1 - yl, 'B': yl}
    z = np.clip(co[vi, 2], HEM_Z, top)
    u = (top - z) / (top - HEM_Z) * NSEG
    i0 = min(int(u), NSEG - 1); f = u - i0
    segw = {i0 + 1: 1 - f}
    if i0 + 2 <= NSEG:
        segw[i0 + 2] = f
    else:
        segw[i0 + 1] = 1.0
    for c, a in cw.items():
        for l, bb in lw.items():
            for i, s_ in segw.items():
                w = ch * a * bb * s_
                if w > 1e-4:
                    W[k, gi[f'Robe_{c}{l}_{i}']] += w
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
for k, vi in enumerate(ids):
    for g in list(me.vertices[vi].groups):
        body.vertex_groups[g.group].remove([int(vi)])
    for j in np.nonzero(W[k] > 1e-3)[0]:
        body.vertex_groups[int(j)].add([int(vi)], float(W[k, j]), 'REPLACE')
print('ROBE chains', len(COLS) * len(LAY) * NSEG, 'bones; cloth vertices', len(ids), 'body share mean', round(float(b.mean()), 2),
      'hood', int(hood.sum()), 'chain top z', round(top, 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
