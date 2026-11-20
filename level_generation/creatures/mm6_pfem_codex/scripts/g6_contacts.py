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
GP = os.path.join(HERE, 'work', 'grip_pose.json')
G = json.load(open(GP)) if os.path.exists(GP) else None    # druidess: no held prop
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
PIECE = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', PIECE)
report = {}
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    worst = {}
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
        P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
        for s in ('L', 'R'):
            keep = ~PARTS[f'{s}_arm_all'] & (PIECE != 100)     # druidess: the cloak is simulated (cloak_sim.py, own gate)
            fl = [fc for fc in faces if all(keep[i] for i in fc)]
            tree = BVHTree.FromPolygons([tuple(p) for p in P], fl)
            samples = {f'{s}_forearm': P[PARTS[f'{s}_forearm']], f'{s}_hand': P[PARTS[f'{s}_hand']]}
            if s == 'R' and G is not None:
                hm = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
                c = hm @ Vector(G['handle_centre_hand_local']); ax = (hm.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
                samples['sword'] = np.array([tuple(c + ax * t) for t in np.linspace(0.06, 0.85, 40)])
            if s == 'R' and G is not None:
                # longest blade that stays out of the body in this frame: first sample (beyond the guard) inside
                for t, p in zip(np.linspace(0.06, 0.85, 40), samples['sword']):
                    loc, nrm, idx, dist = tree.find_nearest(Vector(p), 0.05)
                    if loc is not None and (Vector(p) - loc).dot(nrm) < -0.7 * dist:
                        if t < worst.get('max_clear_blade_m', (9, 0))[0]:
                            worst['max_clear_blade_m'] = (float(t), f)
                        break
            for k, pts in samples.items():
                d, hit_piece = 0.0, None
                for p in pts:
                    loc, nrm, idx, dist = tree.find_nearest(Vector(p), 0.05)
                    if loc is not None and dist > d and (Vector(p) - loc).dot(nrm) < -0.7 * dist:   # behind the face, not beside a thin edge
                        d = dist; hit_piece = int(PIECE[fl[idx][0]])
                if d > worst.get(k, (0, 0))[0]:
                    worst[k] = (d, f, hit_piece)
    report[an] = {k: ((round(v[0], 2) if k == 'max_clear_blade_m' else round(v[0] * 100, 1)),) + tuple(v[1:]) for k, v in worst.items()}
    print('G6', an, 'worst depth cm (frame, piece hit):', report[an])
json.dump(report, open(os.path.join(HERE, 'work', 'g6_contacts.json'), 'w'), indent=1)
