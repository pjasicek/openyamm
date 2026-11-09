"""Numeric gates for the robed casters on every half frame of every clip (adapted from mm8_m460_claude quick_gates.py).
Per clip, the worst value and its frame:
- {s}_arm_p99 / {s}_arm_max: edge stretch (posed / rest length) of the sleeve and arm skin (upper arm/forearm weight
  > 0.3; playbook G4: p99 <~ 2);
- {s}_hand_max: hand shell edge stretch (G5; <~ 4.5);
- {s}_wrist_swing: hand swing against the forearm (deg, arm gate <= 60), {s}_wrist_twist_range;
- robe_p99 / robe_max: robe edge stretch (skirt and chain-weighted robe top);
- {s}_hand_in_body: deepest hand point inside the body surface (signed nearest, robe top/skirt/head faces not
  weighted to that arm; m460 rule: inside when (p - nearest) . n < -0.7 d), metres;
- {s}_hand_banner: closest hand point to a banner face (open shells: proximity only), metres;
- body_floor_min: lowest non-robe, non-banner vertex (m).
Writes review/gates_<tag>.json. Args: -- <blend> <tag> [clip ...]"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
blend, tag, clips = a[0], a[1], a[2:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import cfg
HANDS = cfg.HANDS
BODYG = tuple(int(x) for x in os.environ.get('BODY_GARMENTS', '0,1,2').split(','))
BANNERG = tuple(int(x) for x in os.environ.get('BANNER_GARMENTS', '10').split(','))
NOFLOOR = tuple(int(x) for x in os.environ.get('NOFLOOR_GARMENTS', '2,8,10').split(','))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
P0 = np.array([v.co[:] for v in me.vertices])
pv = np.array([x.value for x in me.attributes['piece'].data]); gv = np.array([x.value for x in me.attributes['garment'].data])
names = [g.name for g in body.vertex_groups]
W = np.zeros((len(P0), len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight


def mask(side, parts, thr):
    ids = [i for i, n in enumerate(names) if n.startswith(f'B_{side}_') and any(t in n for t in parts)]
    return W[:, ids].sum(1) > thr


robe = np.array([sum(W[i, j] for j, n in enumerate(names) if n.startswith('Robe_')) > 0.3 for i in range(len(P0))])
armm = {s: mask(s, ['Clavicle', 'UpperArm', 'Forearm', 'Hand'], 0.2) for s in 'LR'}
JB = lambda n: np.array(rig.data.bones[n].head_local)
handm = {s: cfg.hand_mask(P0, pv, s, JB(f'B_{s}_Hand'), JB(f'B_{s}_Forearm'), 0.0) for s in 'LR'}
stretchm = {s: mask(s, ['UpperArm', 'Forearm'], 0.3) & ~handm[s] for s in 'LR'}
edges = np.array([e.vertices[:] for e in me.edges]); L0 = np.linalg.norm(P0[edges[:, 0]] - P0[edges[:, 1]], axis=1)
ef = {s: stretchm[s][edges[:, 0]] & stretchm[s][edges[:, 1]] for s in 'LR'}
hf = {s: handm[s][edges[:, 0]] & handm[s][edges[:, 1]] for s in 'LR'}
rf = robe[edges[:, 0]] & robe[edges[:, 1]]
faces = [tuple(f.vertices) for f in me.polygons]
bodyf = {s: [f for f in faces if all(gv[i] in BODYG and not handm['L'][i] and not handm['R'][i] and not armm[s][i] for i in f)] for s in 'LR'}
bannerf = [f for f in faces if all(gv[i] in BANNERG for i in f)]
handv = {s: np.where(handm[s])[0] for s in 'LR'}
floorv = ~np.isin(gv, NOFLOOR) & ~robe


def coords():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    v = np.array([tuple(body.matrix_world @ x.co) for x in m.vertices]); ev.to_mesh_clear(); return v


def inside(tree, pts):
    best, where = 0.0, None
    for p in pts:
        loc, n, fi, d = tree.find_nearest(Vector(p), 0.08)
        if loc is not None and (Vector(p) - loc).dot(n) < -0.7 * d and d > best:
            best, where = d, p.tolist()
    return best, where


report = {}
clips = clips or [x for x in ('Standing', 'Walking', 'Attack', 'Cast', 'Hit', 'Death', 'Fidget') if x in bpy.data.actions]
for name in clips:
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    worst = {}; tw = {s: [] for s in 'LR'}; floors = []

    def rec(k, v, f):
        if k not in worst or v > worst[k]['value']:
            worst[k] = {'value': round(float(v), 4), 'frame': float(f)}
    for f in np.arange(act.frame_range[0], act.frame_range[1] + 0.001, 0.5):
        sc.frame_set(int(f), subframe=float(f - int(f))); P = coords()
        st = np.linalg.norm(P[edges[:, 0]] - P[edges[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        rec('robe_p99', np.percentile(st[rf], 99), f); rec('robe_max', st[rf].max(), f)
        btree = BVHTree.FromPolygons(P.tolist(), bannerf) if bannerf else None
        for s in 'LR':
            rec(f'{s}_arm_p99', np.percentile(st[ef[s]], 99), f); rec(f'{s}_arm_max', st[ef[s]].max(), f)
            rec(f'{s}_hand_max', st[hf[s]].max(), f)
            sw, t = armik.wrist_cost(rig, s, armik.W(rig, f'B_{s}_Hand').to_3x3()); rec(f'{s}_wrist_swing', sw, f); tw[s].append(t)
            tree = BVHTree.FromPolygons(P.tolist(), bodyf[s])
            d, where = inside(tree, P[handv[s]]); rec(f'{s}_hand_in_body', d, f)
            if btree is not None:
                dmin = min(btree.find_nearest(Vector(p), 1.0)[3] or 1.0 for p in P[handv[s]][::3])
                rec(f'{s}_hand_banner_close', -dmin, f)
        floors.append(float(P[floorv, 2].min()))
    for s in 'LR':
        v = np.degrees(np.unwrap(np.radians(tw[s]))); worst[f'{s}_wrist_twist_range'] = [round(float(v.min()), 1), round(float(v.max()), 1)]
    worst['body_floor_min'] = round(min(floors), 4)
    report[name] = worst
    print('GATE', name, json.dumps({k: (v['value'] if isinstance(v, dict) else v) for k, v in worst.items()}))
json.dump(report, open(os.path.join(HERE, 'review', f'gates_{tag}.json'), 'w'), indent=1)
