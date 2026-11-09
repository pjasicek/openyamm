"""Attack gates on a review-viewer GLB (body + rigid axe in one skinned mesh), imported as is, sampled at 60 Hz
(after mm8_m604_reduce_claude/scripts/attack_gates.py):
- contacts: axe-head points (Axe-weighted, over 0.85 m from the pommel), handle points (0.10-0.85 m, outside both
  hands' reach of 6 cm), forearm and hand points inside the rest of the body (the arm's own side excluded; horns and
  legs included); inside = behind the nearest face within a 45 deg cone and odd ray parity on 2 of 3 axes;
- hand stretch: max posed/rest edge length on hand/finger edges per side;
- floor: lowest body and axe point; end pose vs Standing frame 0 (max vertex distance).
Usage: blender -b -P attack_gates.py -- <glb> <label> [clip]  -> work/gates_<label>.json"""
import json, os, sys, bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; glb, label = a[:2]; clip = a[2] if len(a) > 2 else 'Attack'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('M484')); me = body.data
names = [g.name for g in body.vertex_groups]; col = {n: i for i, n in enumerate(names)}; nv = len(me.vertices)
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
part = lambda s, keys: Wt[:, [col[n] for n in names if n.startswith(f'B_{s}_') and any(k in n for k in keys)]].sum(1)
AXE = Wt[:, col['Axe']] > .9
rest = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
pommel = np.array(tuple(rig.matrix_world @ rig.data.bones['Axe'].head_local))
along = np.linalg.norm(rest - pommel, axis=1)
HEAD = AXE & (along > .85); HANDLE = AXE & (along > .10) & (along < .85)
print('SAMPLES axe', int(AXE.sum()), 'head', int(HEAD.sum()), 'handle', int(HANDLE.sum()))
faces = [tuple(p.vertices) for p in me.polygons]
E = np.array([tuple(e.vertices) for e in me.edges]); rl = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
hw = Wt[:, [col[n] for n in names if 'Hand' in n or 'Finger' in n]].sum(1)
HE = (hw[E[:, 0]] > .3) & (hw[E[:, 1]] > .3) & ~AXE[E[:, 0]]
side = np.where(rest[E[:, 0], 0] < 0, 'R', 'L')


def inside(tree, point):
    votes = 0
    for axis in [(1, .271, .137), (-.193, 1, .317), (.239, .173, 1)]:
        d = Vector(axis).normalized(); st = Vector(point); hits = 0
        for _ in range(64):
            hit, n_, i_, dist = tree.ray_cast(st, d, 10)
            if hit is None:
                break
            hits += 1; st = hit + d * 1e-5
        votes += hits % 2
    return votes >= 2


def posed():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    c = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear(); return c


act = next(x for x in bpy.data.actions if x.name.split('|')[-1] == clip or x.name == clip)
std = next(x for x in bpy.data.actions if x.name.split('|')[-1] == 'Standing' or x.name == 'Standing')


def use(ac):
    rig.animation_data.action = ac
    if ac.slots:
        rig.animation_data.action_slot = ac.slots[0]


use(std); sc.frame_set(0); P_std = posed()
use(act); f0, f1 = act.frame_range
arm = {s: part(s, ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')) > .2 for s in 'LR'}
fore = {s: part(s, ('Forearm',)) > .5 for s in 'LR'}; hand = {s: part(s, ('Hand', 'Finger')) > .5 for s in 'LR'}
anyarm = arm['L'] | arm['R']
FLOOR = []
R = {'contacts_cm': {}, 'hand_stretch': {'L': 0, 'R': 0}, 'floor_body': 9, 'floor_axe': 9}
for k in range(int(round((f1 - f0) / 24 * 60)) + 1):
    fr = f0 + k / 60 * 24; sc.frame_set(int(fr), subframe=fr - int(fr)); P = posed(); t = round(k / 60, 4)
    if float(P[~AXE, 2].min()) < R['floor_body']:
        R['floor_body'] = float(P[~AXE, 2].min()); R['floor_body_t'] = t
    R['floor_axe'] = min(R['floor_axe'], float(P[AXE, 2].min()))
    FLOOR.append((t, round(float(P[~AXE, 2].min()), 4)))
    r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(rl, 1e-6)
    for s in 'LR':
        m = HE & (side == s)
        if m.any():
            R['hand_stretch'][s] = max(R['hand_stretch'][s], float(r[m].max()))
    if k % 2:
        continue
    trees, flist = {}, {}
    for s, keep in (('L', ~arm['L'] & ~AXE), ('R', ~arm['R'] & ~AXE), ('body', ~anyarm & ~AXE)):
        flist[s] = [fc for fc in faces if all(keep[i] for i in fc)]
        trees[s] = BVHTree.FromPolygons([tuple(p) for p in P], flist[s])
    handpts = np.concatenate([P[hand['L']], P[hand['R']]])
    far = np.array([np.linalg.norm(handpts - p, axis=1).min() > .06 for p in P[HANDLE]])
    samples = [('L', 'L_forearm', P[fore['L']]), ('L', 'L_hand', P[hand['L']]), ('R', 'R_forearm', P[fore['R']]),
               ('R', 'R_hand', P[hand['R']]), ('body', 'axe_head', P[HEAD]), ('body', 'handle', P[HANDLE][far])]
    for tk, key, pts in samples:
        d = 0.0; tree = trees[tk]; where = ''
        for p in pts:
            loc, nrm, idx, dist = tree.find_nearest(Vector(p), 0.05)
            if loc is not None and dist > d and (Vector(p) - loc).dot(nrm) < -0.7 * dist and inside(tree, p):
                d = dist; where = names[int(np.argmax(Wt[flist[tk][idx][0]]))]
        if d * 100 > R['contacts_cm'].get(key, (0, 0))[0]:
            R['contacts_cm'][key] = (round(d * 100, 2), t, where)
sc.frame_set(int(f1)); R['end_vs_standing_mm'] = round(float(np.linalg.norm(posed() - P_std, axis=1).max() * 1000), 1)
R['floor_curve'] = FLOOR[::6]
R = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in R.items()}
json.dump(R, open(os.path.join(HERE, 'work', f'gates_{label}.json'), 'w'), indent=1); print('GATES', label, json.dumps(R))
