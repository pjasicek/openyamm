"""Deformation, contact, floor and jerk gates for every Medusa clip (humanoid G4-G6 + arm/hand gate numbers, quadruped
floor rule) on the animated master. Every second frame (every frame for jerk):
- stretch: max edge length / rest length per region (arms = skin weighted mostly to arm bones, hands = the hand pieces,
  tail/column = serpent skin, hair = the snake pieces, torso = the rest of the skin), p99 and max;
- contacts (G6): hands, bow, arrow and the forearms against the torso/column/head skin - signed distance to the nearest
  skin vertex along its normal; depth > 1 cm counts as inside (the arm's own skin is excluded for its hand);
- floor: lowest vertex of the skin, hair, hands and props (bow, arrow) per clip; tail lift (highest tail-tip vertex);
- jerk: world rotation step of Head, Hand_L, Hand_R and Bow per frame (deg) and its second difference.
Writes review/gates.json and prints one line per clip. Args: <blend>"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
props = {n: bpy.data.objects[n] for n in ('BowMesh', 'ArrowMesh') if n in bpy.data.objects}
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
HAIR = [1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 23, 24, 35]
names = [g.name for g in body.vertex_groups]
W = np.zeros((len(me.vertices), len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
gi = {n: i for i, n in enumerate(names)}
armL = W[:, [gi[n] for n in names if n.endswith('_L') and any(n.startswith(k) for k in ('UpperArm', 'ForeArm', 'Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]].sum(1)
armR = W[:, [gi[n] for n in names if n.endswith('_R') and any(n.startswith(k) for k in ('UpperArm', 'ForeArm', 'Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]].sum(1)
serp = W[:, [gi[n] for n in names if n.startswith(('Tail_', 'Col_', 'Root'))]].sum(1)
skin = pv == 0
REG = {'arms': skin & ((armL > 0.5) | (armR > 0.5)), 'hands': np.isin(pv, [5, 6]), 'serpent': skin & (serp > 0.5),
       'hair': np.isin(pv, HAIR), 'torso': skin & (armL <= 0.5) & (armR <= 0.5) & (serp <= 0.5)}
E = np.array([tuple(e.vertices) for e in me.edges])
rest = np.array([tuple(v.co) for v in me.vertices]); L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
ereg = {k: m[E[:, 0]] & m[E[:, 1]] for k, m in REG.items()}
target = skin & (armL < 0.3) & (armR < 0.3)                     # torso, column and head skin
tip = rest[skin][np.argmin(np.linalg.norm(rest[skin] - [-1.568, 1.65, 0.108], axis=1))]
tailtip = skin & (np.linalg.norm(rest - tip, axis=1) < 0.4)
JB = ['Head', 'Hand_L', 'Hand_R', 'Bow']
rig.animation_data_create()
res = {}


def evaluated(o):
    dg = bpy.context.evaluated_depsgraph_get(); ev = o.evaluated_get(dg); m = ev.to_mesh()
    P = np.array([tuple(o.matrix_world @ v.co) for v in m.vertices]); N = np.array([tuple(v.normal) for v in m.vertices])
    ev.to_mesh_clear(); return P, N


ONLY = os.environ.get('CLIPS')
for act in [x for x in bpy.data.actions if x.name in ('Standing', 'Walking', 'Running', 'Attack', 'Hit', 'Fidget', 'Death', 'Dead') and (not ONLY or x.name in ONLY.split(','))]:
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = map(int, act.frame_range)
    st = {k: [] for k in REG}; cont = {k: 0.0 for k in ('hand_L', 'hand_R', 'forearm_L', 'forearm_R', 'bow', 'arrow')}
    contf = {k: None for k in cont}
    low = {'skin': 9, 'hair': 9, 'hands': 9, 'bow': 9, 'arrow': 9}; tail_hi = 0.0; rots = {b: [] for b in JB}
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        for b in JB:
            rots[b].append((rig.matrix_world @ rig.pose.bones[b].matrix).to_quaternion())
        if (f - f0) % 2 and f != f1:
            continue
        P, N = evaluated(body)
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        for k in REG:
            if ereg[k].any():
                st[k].append((float(np.percentile(r[ereg[k]], 99)), float(r[ereg[k]].max())))
        low['skin'] = min(low['skin'], float(P[skin, 2].min())); low['hair'] = min(low['hair'], float(P[REG['hair'], 2].min()))
        low['hands'] = min(low['hands'], float(P[REG['hands'], 2].min()))
        tail_hi = max(tail_hi, float(P[tailtip, 2].max()))
        ids = np.where(target)[0]; kd = KDTree(len(ids))
        for k, i in enumerate(ids):
            kd.insert(P[i], k)
        kd.balance()

        def depth(Q, exclude=None):
            dmax = 0.0
            for q in Q:
                co_, k, d = kd.find(q)
                i = ids[k]
                if exclude is not None and exclude[i]:
                    continue
                s = float(np.dot(q - P[i], N[i]))
                if s < 0:
                    dmax = max(dmax, -s if d < 0.06 else 0.0)
            return dmax
        for side, arm_w in (('L', armL), ('R', armR)):
            hand = P[(pv == (5 if side == 'L' else 6))]
            d = depth(hand[::2]); cont['hand_' + side] = max(cont['hand_' + side], d)
            if os.environ.get('VERBOSE'):
                print('FRAME', act.name, f, side, 'hand depth cm', round(100 * d, 1))
            if d >= cont['hand_' + side] and d > 0.01:
                contf['hand_' + side] = f
            fa = P[skin & (arm_w > 0.8) & (W[:, gi['ForeArm_' + side]] + W[:, gi['ForeArmTwist_' + side]] > 0.5)]
            d = depth(fa[::3]); cont['forearm_' + side] = max(cont['forearm_' + side], d)
            if d >= cont['forearm_' + side] and d > 0.01:
                contf['forearm_' + side] = f
        for nm, o in props.items():
            Q, _ = evaluated(o)
            key = 'bow' if 'Bow' in nm else 'arrow'
            if key == 'arrow':
                s = rig.pose.bones['Arrow'].matrix.to_scale()
                if s.length < 1e-3:
                    continue
            low[key] = min(low[key], float(Q[:, 2].min()))
            d = depth(Q[::3]); cont[key] = max(cont[key], d)
            if d >= cont[key] and d > 0.01:
                contf[key] = f
    jerk = {}
    for b, qs in rots.items():
        step = [min(a_, 360 - a_) for a_ in (math.degrees(qs[i].rotation_difference(qs[i + 1]).angle) for i in range(len(qs) - 1))]
        jerk[b] = {'step_max': round(max(step), 1) if step else 0, 'accel_max': round(max(abs(step[i + 1] - step[i]) for i in range(len(step) - 1)), 1) if len(step) > 1 else 0}
    res[act.name] = {'stretch': {k: {'p99': round(max(x[0] for x in v), 2), 'max': round(max(x[1] for x in v), 2)} for k, v in st.items() if v},
                     'contact_cm': {k: round(100 * v, 1) for k, v in cont.items()}, 'contact_frame': contf,
                     'floor_low_cm': {k: (round(100 * v, 1) if v < 9 else None) for k, v in low.items()},
                     'tail_tip_high_cm': round(100 * tail_hi, 1), 'jerk_deg_per_frame': jerk}
    print('GATE', act.name, json.dumps(res[act.name]), flush=True)
os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
old = json.load(open(os.path.join(HERE, 'review', 'gates.json'))) if ONLY and os.path.exists(os.path.join(HERE, 'review', 'gates.json')) else {}
old.update(res)
json.dump(old, open(os.path.join(HERE, 'review', 'gates.json'), 'w'), indent=1)
