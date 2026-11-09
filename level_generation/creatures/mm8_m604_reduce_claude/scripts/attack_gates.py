"""Attack gates on a review-viewer GLB (body + rigid sword in one skinned mesh), imported as is, sampled at 60 Hz:
- contacts (mm8_m604_claude/scripts/g6_sword_surface.py method): blade points (Sword-weighted, > 9 cm past the
  joint along the bone) and forearm / hand points inside the rest of the body (arm's own side excluded); inside =
  behind the nearest face within a 45 deg cone and odd ray parity on 2 of 3 axes;
- hand stretch (g5_hand_stretch.py): max posed/rest edge length on hand/finger edges per side;
- cloth: max posed/rest edge length on the mantle and tabard (cloth-region pieces);
- floor: lowest body and sword point; end pose vs Standing frame 0 (max vertex distance).
Usage: blender -b -P attack_gates.py -- <glb> <label> [clip]  -> work/gates_<label>.json"""
import json, os, sys, bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; glb, label = a[:2]; clip = a[2] if len(a) > 2 else 'Attack'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('EtherKnight')); me = body.data
names = [g.name for g in body.vertex_groups]; col = {n: i for i, n in enumerate(names)}; nv = len(me.vertices)
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
part = lambda s, keys: Wt[:, [col[n] for n in names if n.startswith(f'B_{s}_') and any(k in n for k in keys)]].sum(1)
SWORD = Wt[:, col['Sword']] > .9
rest = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
sb = rig.data.bones['Sword']; LOC = np.array([tuple(sb.matrix_local.inverted() @ (rig.matrix_world.inverted() @ Vector(p))) for p in rest])
BLADE = SWORD & (LOC[:, 1] > .09)
print('SAMPLES sword', int(SWORD.sum()), 'blade', int(BLADE.sum()), 'sword local y range', LOC[SWORD, 1].min().round(3), LOC[SWORD, 1].max().round(3))
faces = [tuple(p.vertices) for p in me.polygons]
E = np.array([tuple(e.vertices) for e in me.edges]); rl = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
hw = Wt[:, [col[n] for n in names if 'Hand' in n or 'Finger' in n]].sum(1)
HE = (hw[E[:, 0]] > .3) & (hw[E[:, 1]] > .3) & ~SWORD[E[:, 0]]
side = np.where(rest[E[:, 0], 0] < 0, 'R', 'L')
# cloth: the mantle shell and tabard strips of the welded source mesh (work/mesh_in.npz components), mapped to the
# imported vertices by nearest source vertex (the import keeps seam splits, so its own connectivity is fragmented)
from mathutils.kdtree import KDTree
src = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); sv, sf = src['verts'], src['faces']
par = np.arange(len(sv))
def root_of(i):
    while par[i] != i:
        par[i] = par[par[i]]; i = par[i]
    return i
for x, y in np.concatenate([sf[:, [0, 1]], sf[:, [1, 2]]]):
    rx, ry = root_of(int(x)), root_of(int(y))
    if rx != ry: par[rx] = ry
lab = np.array([root_of(i) for i in range(len(sv))]); size = np.bincount(lab, minlength=len(sv))
cloth_lab = [c for c in np.unique(lab) if (size[c] > 600 and abs(sv[lab == c, 2].mean() - 1.5) < .06)
             or (100 < size[c] < 200 and abs(sv[lab == c, 2].mean() - .8) < .06 and abs(sv[lab == c, 1].mean()) > .08)]
kd = KDTree(len(sv))
for i, p in enumerate(sv):
    kd.insert(p, i)
kd.balance()
nearest = [kd.find(p) for p in rest]
near = np.array([q[1] for q in nearest]); dist = np.array([q[2] for q in nearest])
CLOTHV = np.isin(lab[near], cloth_lab) & (dist < .01) & ~SWORD
CE = CLOTHV[E[:, 0]] & CLOTHV[E[:, 1]]
print('CLOTH vertices', int(CLOTHV.sum()), 'edges', int(CE.sum()))
def inside(tree, point):
    votes = 0
    for axis in [(1, .271, .137), (-.193, 1, .317), (.239, .173, 1)]:
        d = Vector(axis).normalized(); st = Vector(point); hits = 0
        for _ in range(64):
            hit, n_, i_, dist = tree.ray_cast(st, d, 10)
            if hit is None: break
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
    if ac.slots: rig.animation_data.action_slot = ac.slots[0]
use(std); sc.frame_set(0); P_std = posed()
use(act); f0, f1 = act.frame_range
arm = {s: part(s, ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')) > .2 for s in 'LR'}
fore = {s: part(s, ('Forearm',)) > .5 for s in 'LR'}; hand = {s: part(s, ('Hand', 'Finger')) > .5 for s in 'LR'}
FLOOR = []
R = {'contacts_cm': {}, 'hand_stretch': {'L': 0, 'R': 0}, 'cloth_stretch': 0, 'floor_body': 9, 'floor_sword': 9}
for k in range(int((f1 - f0) / 24 * 60) + 1):
    fr = f0 + k / 60 * 24; sc.frame_set(int(fr), subframe=fr - int(fr)); P = posed(); t = round(k / 60, 4)
    if float(P[~SWORD, 2].min()) < R['floor_body']:
        R['floor_body'] = float(P[~SWORD, 2].min()); R['floor_body_t'] = t
    R['floor_sword'] = min(R['floor_sword'], float(P[SWORD, 2].min()))
    FLOOR.append((t, round(float(P[~SWORD, 2].min()), 4)))
    r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(rl, 1e-6)
    for s in 'LR':
        m = HE & (side == s)
        if m.any(): R['hand_stretch'][s] = max(R['hand_stretch'][s], float(r[m].max()))
    R['cloth_stretch'] = max(R['cloth_stretch'], float(r[CE].max()))
    if k % 2:
        continue
    for s in 'LR':
        keep = ~arm[s] & ~SWORD
        fl = [fc for fc in faces if all(keep[i] for i in fc)]
        tree = BVHTree.FromPolygons([tuple(p) for p in P], fl)
        samples = {f'{s}_forearm': P[fore[s]], f'{s}_hand': P[hand[s]]}
        if s == 'R':
            samples['blade'] = P[BLADE]
        for key, pts in samples.items():
            d = 0.0
            for p in pts:
                loc, nrm, idx, dist = tree.find_nearest(Vector(p), 0.05)
                if loc is not None and dist > d and (Vector(p) - loc).dot(nrm) < -0.7 * dist and inside(tree, p):
                    d = dist
            if d * 100 > R['contacts_cm'].get(key, (0, 0))[0]:
                R['contacts_cm'][key] = (round(d * 100, 2), t)
sc.frame_set(int(f1)); R['end_vs_standing_mm'] = round(float(np.linalg.norm(posed() - P_std, axis=1).max() * 1000), 1)
R['floor_curve'] = FLOOR[::3]
R = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in R.items()}
json.dump(R, open(os.path.join(HERE, 'work', f'gates_{label}.json'), 'w'), indent=1); print('GATES', label, json.dumps(R))
