"""G6 contacts: per frame of each action, how deep the forearms, hands (with fingers) and the sword blade go into the
rest of the body (torso, hips, legs, armour; the arm's own side excluded). Inside test: closest point on the posed
body BVH and its face normal; a sample is inside if it lies behind the closest face within a 45 deg cone of its normal
((p - closest) . normal < -0.7 |p - closest|, within 5 cm); a plain sign test flagged points beside thin belts. Sword: points along the
handle axis (work/grip_pose.json, hand-local) from the guard (+6 cm) to the tip (+85 cm), blade on the axis' positive
side. Prints per action the worst depth (cm) and frame for each part, and writes work/g6_contacts.json.
Args: -- <blend> action [action ...]"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
blend, acts = a[0], a[1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
_GP = os.path.join(HERE, 'work', 'grip_pose.json')
G = json.load(open(_GP)) if os.path.exists(_GP) else None   # m362: unarmed, no blade samples
names = [g.name for g in body.vertex_groups]
nv = len(me.vertices)
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
col = {n: i for i, n in enumerate(names)}
def part(side, keys):
    return Wt[:, [col[n] for n in names if n.startswith(f'B_{side}_') and any(k in n for k in keys)]].sum(1)
PARTS = {}
for s in ('L', 'R'):
    PARTS[f'{s}_forearm'] = part(s, ('Forearm',)) > 0.5
    PARTS[f'{s}_hand'] = part(s, ('Hand', 'Finger')) > 0.5
    PARTS[f'{s}_arm_all'] = part(s, ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')) > 0.2
faces = [tuple(p.vertices) for p in me.polygons]
PIECE = np.zeros(nv, np.int32); me.attributes['garment'].data.foreach_get('value', PIECE)   # natm: reports the garment hit
# natm buckler (export_runtime.py frame): back plate on the left forearm's outer side at 60 %, on B_L_ForearmTwist
import math as _m
_fa, _ha = rig.data.bones['B_L_Forearm'].head_local, rig.data.bones['B_L_Hand'].head_local
_BY = (_ha - _fa).normalized(); _BZ = Vector((1, 0, 0)); _BZ = (_BZ - _BY * _BZ.dot(_BY)).normalized(); _BX = _BY.cross(_BZ)
_BO = _fa + (_ha - _fa) * 0.6 + _BZ * 0.045
BUCK_REST = [_BO + _BX * (0.21 * s_ * _m.cos(t_)) + _BY * (0.25 * s_ * _m.sin(t_)) + _BZ * (0.02 + 0.065 * (1 - s_ * s_))
             for s_ in (0.5, 1.0) for t_ in np.linspace(0, 2 * _m.pi, 20, endpoint=False)]
SPEAR_T = np.linspace(0.06, 0.85, 40)          # m362 scimitar: guard -> tip along the handle axis (straight chord)
report = {}
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    worst = {}
    for f in np.arange(f0, f1 + 0.01, 0.5):
        bpy.context.scene.frame_set(int(f), subframe=float(f - int(f)))
        deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
        P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
        for s in ('L', 'R'):
            keep = ~PARTS[f'{s}_arm_all']
            # m362: the skin (garment 0: body + arm shells) is closed - inside test; helmet, guard, panels, trim, links - proximity
            fl = [fc for fc in faces if all(keep[i] for i in fc) and PIECE[fc[0]] == 0]
            tree = BVHTree.FromPolygons([tuple(p) for p in P], fl)
            fs = [fc for fc in faces if all(keep[i] for i in fc) and PIECE[fc[0]] != 0]
            shell = BVHTree.FromPolygons([tuple(p) for p in P], fs)
            samples = {f'{s}_forearm': P[PARTS[f'{s}_forearm']], f'{s}_hand': P[PARTS[f'{s}_hand']]}
            if s == 'R' and G is not None:
                hm = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
                c = hm @ Vector(G['handle_centre_hand_local']); ax = (hm.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
                samples['sword'] = np.array([tuple(c + ax * t) for t in SPEAR_T])
            for k, pts in samples.items():
                d, hit_piece, where = 0.0, None, None
                for j, p in enumerate(pts):
                    loc, nrm, idx, dist = tree.find_nearest(Vector(p), 0.06)   # m362: 0.15 m flagged a blade 13 cm off a fingertip as inside
                    if loc is not None and dist > d and (Vector(p) - loc).dot(nrm) < -0.7 * dist:   # behind the face, not beside a thin edge
                        d = dist; hit_piece = int(PIECE[fl[idx][0]]); where = round(float(SPEAR_T[j]), 2) if k == 'sword' else j
                if d > worst.get(k, (0, 0))[0]:
                    worst[k] = (d, float(f), hit_piece, where)
                # open shells: the shaft (r 1.4 cm) or a limb vertex closer than RAD to a card counts as a crossing
                rad = 0.012 if k == 'sword' else 0.003
                n_close = 0
                for j, p in enumerate(pts):
                    loc, nrm, idx, dist = shell.find_nearest(Vector(p), rad)
                    if loc is not None:
                        n_close += 1
                key = k + '_shell'
                if n_close > worst.get(key, (0, 0))[0]:
                    worst[key] = (n_close, float(f), int(PIECE[fs[idx][0]]) if loc is not None else None)
    report[an] = {k: ((round(v[0] * 100, 1),) if not k.endswith('_shell') else (v[0],)) + tuple(v[1:]) for k, v in worst.items()}
    print('G6', an, 'worst depth cm (frame, piece hit):', report[an])
json.dump(report, open(os.path.join(HERE, 'work', 'g6_contacts.json'), 'w'), indent=1)
