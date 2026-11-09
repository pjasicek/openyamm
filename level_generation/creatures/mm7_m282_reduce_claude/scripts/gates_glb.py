"""The batch I gates (../mm7_m282_claude/scripts/gates.py) straight from a runtime GLB's LOD0, so the reduced export
and the batch I export are measured the same way. Every second frame of every clip:
- edge stretch (posed / rest length, edges over 1 mm) per region: arms (skin mostly on arm bones), hands (pieces 5/6),
  serpent (skin on Tail/Col/Root), hair (the 17 snakes), torso (the rest of the skin); p99 and max;
- contacts (G6): signed depth of hand and forearm vertices inside the torso/column/head skin (the nearest skin vertex
  within 6 cm, along its normal, as batch I; REA_SURFACE=1: below the nearest skin surface point); bow and arrow are separate attachments here (unchanged files, hands bit-identical);
- floor: lowest skin, hair and hand vertex per clip, and the highest rattle-tip vertex (tail never leaves the floor).
Piece labels per vertex come from work/master_pieces.npz (nearest rest vertex of the batch I master).
Usage: blender -b -P gates_glb.py -- <glb> <label>  -> work/gates_<label>.json"""
import bpy, json, os, sys
import numpy as np
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
body = bpy.data.objects['M282']; rig = next(m.object for m in body.modifiers if m.type == 'ARMATURE'); me = body.data
m = np.load(os.path.join(HERE, 'work', 'master_pieces.npz'))
kd = KDTree(len(m['P']))
for i, p in enumerate(m['P']):
    kd.insert(p, i)
kd.balance()
rest = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
pv = np.array([m['piece'][kd.find(p)[1]] for p in rest])
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
W = np.zeros((len(me.vertices), len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
ARM = ('UpperArm', 'ForeArm', 'Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
armL = W[:, [gi[n] for n in names if n.endswith('_L') and n.startswith(ARM)]].sum(1)
armR = W[:, [gi[n] for n in names if n.endswith('_R') and n.startswith(ARM)]].sum(1)
serp = W[:, [gi[n] for n in names if n.startswith(('Tail_', 'Col_', 'Root'))]].sum(1)
HAIR = [1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 23, 24, 35]
skin = pv == 0
REG = {'arms': skin & ((armL > 0.5) | (armR > 0.5)), 'hands': np.isin(pv, [5, 6]), 'serpent': skin & (serp > 0.5),
       'hair': np.isin(pv, HAIR), 'torso': skin & (armL <= 0.5) & (armR <= 0.5) & (serp <= 0.5)}
E = np.array([tuple(e.vertices) for e in me.edges]); L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
ok = L0 > 1e-3
ereg = {k: x[E[:, 0]] & x[E[:, 1]] & ok for k, x in REG.items()}
target = skin & (armL < 0.3) & (armR < 0.3)
tip = rest[skin][np.argmin(np.linalg.norm(rest[skin] - [-1.568, 1.65, 0.108], axis=1))]
tailtip = skin & (np.linalg.norm(rest - tip, axis=1) < 0.4)
# REA_SURFACE=1: depth below the nearest point of the target skin surface (BVH, face normal) instead of the nearest
# skin vertex's tangent plane; the vertex rule reads a forearm beside a decimated (sparser) belly as 4-5 cm inside
SURFACE = os.environ.get('REA_SURFACE') == '1'
from mathutils.bvhtree import BVHTree  # noqa: E402
tfaces = [tuple(p.vertices) for p in me.polygons if all(target[i] for i in p.vertices)]
res = {}
for act in sorted(bpy.data.actions, key=lambda a: a.name):
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = map(int, act.frame_range)
    st = {k: [] for k in REG}; cont = {k: 0.0 for k in ('hand_L', 'hand_R', 'forearm_L', 'forearm_R')}
    low = {'skin': 9, 'hair': 9, 'hands': 9}; tail_hi = 0.0
    for f in list(range(f0, f1 + 1, 2)) + ([f1] if (f1 - f0) % 2 else []):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); mm = ev.to_mesh()
        P = np.array([tuple(body.matrix_world @ v.co) for v in mm.vertices]); N = np.array([tuple(v.normal) for v in mm.vertices])
        ev.to_mesh_clear()
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        for k in REG:
            if ereg[k].any():
                st[k].append((float(np.percentile(r[ereg[k]], 99)), float(r[ereg[k]].max())))
        low['skin'] = min(low['skin'], float(P[skin, 2].min())); low['hair'] = min(low['hair'], float(P[REG['hair'], 2].min()))
        low['hands'] = min(low['hands'], float(P[REG['hands'], 2].min())); tail_hi = max(tail_hi, float(P[tailtip, 2].max()))
        if SURFACE:
            bvh = BVHTree.FromPolygons([tuple(x) for x in P], tfaces)

            def depth(Q):
                dmax = 0.0
                for q in Q:
                    loc, nrm, _, d = bvh.find_nearest(q, 0.06)
                    if loc is not None:
                        s = float(np.dot(q - np.array(loc), np.array(nrm)))
                        if s < 0:
                            dmax = max(dmax, -s)
                return dmax
        else:
            ids = np.where(target)[0]; t = KDTree(len(ids))
            for k, i in enumerate(ids):
                t.insert(P[i], k)
            t.balance()

            def depth(Q):
                dmax = 0.0
                for q in Q:
                    _, k, d = t.find(q); i = ids[k]; s = float(np.dot(q - P[i], N[i]))
                    if s < 0 and d < 0.06:
                        dmax = max(dmax, -s)
                return dmax
        for side, arm_w in (('L', armL), ('R', armR)):
            cont['hand_' + side] = max(cont['hand_' + side], depth(P[pv == (5 if side == 'L' else 6)][::2]))
            fa = skin & (arm_w > 0.8) & (W[:, gi['ForeArm_' + side]] + W[:, gi['ForeArmTwist_' + side]] > 0.5)
            cont['forearm_' + side] = max(cont['forearm_' + side], depth(P[fa][::3]))
    res[act.name] = {'stretch': {k: {'p99': round(max(x[0] for x in v), 2), 'max': round(max(x[1] for x in v), 2)} for k, v in st.items() if v},
                     'contact_cm': {k: round(100 * v, 1) for k, v in cont.items()},
                     'floor_low_cm': {k: round(100 * v, 1) for k, v in low.items()}, 'tail_tip_high_cm': round(100 * tail_hi, 1)}
    print('GATE', act.name, json.dumps(res[act.name]), flush=True)
json.dump(res, open(os.path.join(HERE, 'work', f'gates_{label}{"_surface" if SURFACE else ""}.json'), 'w'), indent=1)
