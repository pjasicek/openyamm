"""m438: closed skin = garment 0 + the trousers (2); rope, bones, teeth and eyes are proximity shells. G6 contacts (adapted from mm7_m214_claude g6_bow.py): per half frame of each action, how deep the prop (piece 100: spear),
the arrow (101, only while visible), the string (102) and both forearms/hands go into the body skin (garment 0:
head/torso, vest, trousers, shins/feet; the sampled arm's own side and the props excluded). Inside test: closest point on
the posed skin and its face normal, inside if behind the face within a 45 deg cone, within 5 cm. Open accessory shells
(quiver, straps, pouches, hair) count as proximity hits (< 3 mm). Also the lowest bow point against the floor.
Writes work/g6_bow.json. Args: -- <blend> action [action ...]"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
blend, acts = a[0], a[1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
names = [g.name for g in body.vertex_groups]
nv = len(me.vertices)
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
col = {n: i for i, n in enumerate(names)}
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
DOM = [names[int(np.argmax(Wt[i]))] for i in range(nv)]          # dominant bone per vertex (reported for a hit)
gv = np.zeros(nv, np.int32); me.attributes['garment'].data.foreach_get('value', gv)


def part(side, keys):
    return Wt[:, [col[n] for n in names if n.startswith(f'B_{side}_') and any(k in n for k in keys)]].sum(1)


ARM = {s: part(s, ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')) > 0.2 for s in 'LR'}
SAMPLES = {'prop': pv == 1000, 'arrow': pv == 1001, 'string': pv == 1002}
SAMPLES = {k: m for k, m in SAMPLES.items() if m.any()}
for s in 'LR':
    SAMPLES[f'{s}_forearm'] = (part(s, ('Forearm',)) > 0.5) & (gv == 0)
    SAMPLES[f'{s}_hand'] = (part(s, ('Hand', 'Finger')) > 0.5) & (gv == 0)
faces = [tuple(p.vertices) for p in me.polygons]
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
        arrow_on = 'Arrow' in rig.pose.bones and rig.pose.bones['Arrow'].matrix.to_scale().length > 0.5
        lowest_bow = float(P[SAMPLES['prop'], 2].min())
        if lowest_bow < worst.get('prop_floor', (1e9,))[0]:
            worst['prop_floor'] = (lowest_bow, float(f))
        trees = {}
        for excl in ('L', 'R', None):
            keep = np.isin(gv, (0, 2)) & (pv < 1000)          # m438: the trousers are a closed tube (inside test)
            if excl:
                keep &= ~ARM[excl]
            fl = [fc for fc in faces if all(keep[i] for i in fc)]
            shell_keep = ~np.isin(gv, (0, 2, 9))                       # m438: rope, stump and shin bones, teeth, eyes
            fs = [fc for fc in faces if all(shell_keep[i] for i in fc)]
            trees[excl] = (BVHTree.FromPolygons([tuple(p) for p in P], fl), fl,
                           BVHTree.FromPolygons([tuple(p) for p in P], fs), fs)
        for k, mask in SAMPLES.items():
            if k == 'arrow' and not arrow_on:
                continue
            excl = k[0] if k[1] == '_' else os.environ.get('PROP_HAND', 'L')
            tree, fl, shell, fs = trees[excl]
            pts = P[mask]
            d, hit = 0.0, None
            close = 0
            for p in pts:
                loc, nrm, idx, dist = tree.find_nearest(Vector(p), 0.05)
                if loc is not None and dist > d and (Vector(p) - loc).dot(nrm) < -0.7 * dist:
                    d = dist; hit = DOM[fl[idx][0]]
                loc, nrm, idx, dist = shell.find_nearest(Vector(p), 0.003)
                if loc is not None:
                    close += 1
            if d > worst.get(k, (0,))[0]:
                worst[k] = (d, float(f), hit)
            if close > worst.get(k + '_shell', (0,))[0]:
                worst[k + '_shell'] = (close, float(f))
    report[an] = {k: (round(v[0] * 100, 1) if not k.endswith('_shell') else v[0],) + tuple(v[1:]) for k, v in worst.items()}
    print('G6BOW', an, 'worst depth cm (frame, piece hit):', json.dumps(report[an]))
json.dump(report, open(os.path.join(HERE, 'work', 'g6_bow.json'), 'w'), indent=1)
