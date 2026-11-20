"""G6 contacts: per frame of each action, how deep the forearms, hands (with fingers) and the sword blade go into the
rest of the body (torso, hips, legs, armour; the arm's own side excluded). Inside test: closest point on the posed
body BVH and its face normal; a sample is inside if it lies behind the closest face within a 45 deg cone of its normal
((p - closest) . normal < -0.7 |p - closest|, within 5 cm); a plain sign test flagged points beside thin belts. Sword: points along the
handle axis (work/grip_pose.json, hand-local) from the guard (+6 cm) to the tip (+85 cm), blade on the axis' positive
side. Prints per action the worst depth (cm) and frame for each part, and writes work/g6_contacts.json.
m398: closed shells (bones, boots, skull, helmet: garments 0, 4, 5, 6) get the inside test, the open cuirass and
breeches (1, 3) proximity; sword samples from the guard (+6 cm) to the tip (+52 cm); no buckler.
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
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
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
SPEAR_T = np.linspace(-0.95, 0.55, 40)
CLOSED = (1, 5)                   # m270: plate and gold belt pieces are closed; skirt, arms, head open
def inside(tree, p, n=3):
    # m398: ray parity confirms the cone test (a flat back-rib piece 13 cm away passed the cone test at its rim)
    votes = 0
    for d in ((0.3, 0.5, 0.81), (-0.6, 0.2, -0.77), (0.1, -0.95, 0.3))[:n]:
        o = Vector(p); dv = Vector(d).normalized(); hits = 0
        for _ in range(64):
            loc, nrm, idx, dist = tree.ray_cast(o, dv)
            if loc is None:
                break
            hits += 1; o = loc + dv * 1e-5
        votes += hits % 2
    return votes >= 2


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
            # natm: the skin (garment 0) is closed - inside test; feather cards and panels are open shells - proximity
            fl = [fc for fc in faces if all(keep[i] for i in fc) and PIECE[fc[0]] in CLOSED]
            tree = BVHTree.FromPolygons([tuple(p) for p in P], fl)
            fs = [fc for fc in faces if all(keep[i] for i in fc) and PIECE[fc[0]] not in CLOSED]
            shell = BVHTree.FromPolygons([tuple(p) for p in P], fs)
            samples = {f'{s}_forearm': P[PARTS[f'{s}_forearm']], f'{s}_hand': P[PARTS[f'{s}_hand']]}
            if s == 'R':
                hm = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
                c = hm @ Vector(G['handle_centre_hand_local']); ax = (hm.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
                samples['sword'] = np.array([tuple(c + ax * t) for t in SPEAR_T])
            for k, pts in samples.items():
                d, hit_piece, where = 0.0, None, None
                for j, p in enumerate(pts):
                    loc, nrm, idx, dist = tree.find_nearest(Vector(p), 0.15)
                    if loc is not None and dist > d and (Vector(p) - loc).dot(nrm) < -0.7 * dist and inside(tree, p):   # behind the face, not beside a thin edge
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
