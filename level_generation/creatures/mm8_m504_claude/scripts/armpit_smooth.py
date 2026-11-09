"""Armpit and lat weight smoothing on the textured master (run in build_runtime.sh after sync_actions, so the UVs of
rig_v6 are kept). The overhead raise of the Attack (and the Fidget's flex) stretched the side of the chest and the
inner upper arm to 2-3x (user review: smeared stone texture under both arms): Meshy's weights hand the lat from
B_*_Clavicle / B_*_UpperArm to B_Spine* within a few centimetres. Here, first the clavicle weight fades with the distance from the shoulder joint (full within CL_IN, none beyond CL_OUT; the
removed weight goes to the spine bone at the vertex's height: Meshy gave the clavicles 60-77 % of the chest and lats
down to 26 cm below the shoulder, so the overhead raise dragged the whole side of the torso), then the weights are Laplacian-smoothed
(edge neighbours, ITER iterations of ALPHA), which spreads that hand-over over a wider band:
- region: the torso (TORSO=1, the build's setting; TORSO=0: only vertices with a shoulder weight between 0.02 and
  0.98), grown by GROW edge rings; a falloff of the last rings keeps the border continuous;
- kept out: the head and neck (B_Head + B_Neck > 0.3, the head stays free of the shoulders), the forearms and fists
  (B_*_Forearm*, B_*_Hand weight > 0.3) and the legs (any thigh weight > 0.3);
- weights pruned to 4 per vertex and renormalised.
Prints the edge-stretch p99 / count above 2x of the Attack and Fidget at their worst frame before and after.
Build setting: CL_IN=0.10 CL_OUT=0.25 ITER=40 TORSO=1 (Attack p99 2.44 -> 2.00, edges above 2x 246 -> 135).
Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
ITER = int(os.environ.get('ITER', '40')); ALPHA = float(os.environ.get('ALPHA', '0.5'))
GROW = int(os.environ.get('GROW', '6'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
nv = len(me.vertices); names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
E = np.array([tuple(e.vertices) for e in me.edges])
rest = np.array([tuple(v.co) for v in me.vertices])


def cols(pred):
    return [i for i, n in enumerate(names) if pred(n)]


SH = cols(lambda n: any(k in n for k in ('Clavicle', 'UpperArm')))
HEAD = cols(lambda n: n in ('B_Head', 'B_Neck'))
FAR = cols(lambda n: 'Forearm' in n or n.endswith('Hand') or 'Finger' in n)
LEG = cols(lambda n: any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe')))


def stretch(action):
    act = bpy.data.actions[action]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    worst = (0, 0, 0)
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        pos = np.empty(nv * 3); m.vertices.foreach_get('co', pos); pos = pos.reshape(-1, 3); ev.to_mesh_clear()
        r = np.linalg.norm(pos[E[:, 0]] - pos[E[:, 1]], axis=1) / np.maximum(np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1), 1e-9)
        p = (round(float(np.percentile(r, 99)), 2), int((r > 2).sum()), f)
        worst = max(worst, p)
    rig.animation_data.action = None
    return worst


def report(tag):
    print('ARMPIT', tag, {a: stretch(a) for a in ('Attack', 'Fidget', 'Standing', 'Walking', 'Hit')}, flush=True)


report('before (p99, edges > 2x, frame)')
# 1. clavicle fade: full within CL_IN of the shoulder joint (the clavicle's tail), none beyond CL_OUT; the removed
#    weight goes to the spine bone at the vertex's height (Meshy gave the clavicles most of the chest and lats)
CL_IN = float(os.environ.get('CL_IN', '0.12')); CL_OUT = float(os.environ.get('CL_OUT', '0.30'))
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
spine = [(rig.matrix_world @ rig.data.bones[n].head_local).z for n in ('B_Spine', 'B_Spine1', 'B_Spine2')]
sp_col = np.where(co[:, 2] >= spine[2], gi['B_Spine2'], np.where(co[:, 2] >= spine[1], gi['B_Spine1'], gi['B_Spine']))
if CL_OUT > 0:
    for sd in 'LR':
        c = gi[f'B_{sd}_Clavicle']; j = np.array(rig.matrix_world @ rig.data.bones[f'B_{sd}_Clavicle'].tail_local)
        d = np.linalg.norm(co - j, axis=1); cap = np.clip((CL_OUT - d) / (CL_OUT - CL_IN), 0, 1)
        moved = W[:, c] * (1 - cap); W[:, c] -= moved
        np.add.at(W, (np.arange(nv), sp_col), moved)
    print('ARMPIT clavicle fade', CL_IN, CL_OUT, flush=True)
sh = W[:, SH].sum(1)
seed = ((sh > 0.02) & (sh < 0.98)) | (os.environ.get('TORSO', '1') == '1')
keep_out = (W[:, HEAD].sum(1) > 0.3) | (W[:, FAR].sum(1) > 0.3) | (W[:, LEG].sum(1) > 0.3)
# grow the seed by edge rings; ring k gets the falloff weight
ring = np.full(nv, -1); ring[seed] = 0; cur = seed.copy()
for k in range(1, GROW + 1):
    nb = np.zeros(nv, bool); nb[E[:, 0][cur[E[:, 1]]]] = True; nb[E[:, 1][cur[E[:, 0]]]] = True
    new = nb & (ring < 0); ring[new] = k; cur = new
region = (ring >= 0) & ~keep_out
fall = np.where(ring <= GROW // 2, 1.0, 1.0 - (ring - GROW // 2) / (GROW - GROW // 2 + 1))
a = ALPHA * fall * region
deg = np.bincount(E.ravel(), minlength=nv).astype(float)
for _ in range(ITER):
    S = np.zeros_like(W); np.add.at(S, E[:, 0], W[E[:, 1]]); np.add.at(S, E[:, 1], W[E[:, 0]])
    M = S / np.maximum(deg, 1)[:, None]
    W = W + a[:, None] * (M - W)
top4 = np.argsort(-W, 1)[:, :4]; W2 = np.zeros_like(W); rows = np.arange(nv)[:, None]
W2[rows, top4] = W[rows, top4]; W2 /= np.maximum(W2.sum(1, keepdims=True), 1e-9)
for g in body.vertex_groups:
    g.remove(list(range(nv)))
for j, g in enumerate(body.vertex_groups):
    idx = np.nonzero(W2[:, j] > 1e-4)[0]
    for i in idx:
        g.add([int(i)], float(W2[i, j]), 'REPLACE')
print('ARMPIT region vertices', int(region.sum()), 'iter', ITER, 'alpha', ALPHA, 'grow', GROW, flush=True)
report('after')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
