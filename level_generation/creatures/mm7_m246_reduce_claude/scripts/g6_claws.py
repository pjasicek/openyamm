"""G6 contacts (Behemoth): per frame of each action, how deep each side's forearm and hand (paw + the three claws) go
into the rest of the skin (piece 0, the other arm included, the arm's own side excluded). Inside test as natm's
g6_contacts.py: closest point on the posed skin and its face normal, inside if behind the face within a 45 deg cone
(within 15 cm). Mane shingles are open cards: counted when a claw/forearm vertex comes within 5 mm of one.
Prints per action the worst depth (cm), frame and the bone that owns the hit skin. Writes work/g6_claws.json.
Args: -- <blend> [STEP env, default 1 frame] action [action ...]"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
blend, acts = a[0], a[1:]
STEP = float(os.environ.get('STEP', '1'))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
names = [g.name for g in body.vertex_groups]; nv = len(me.vertices)
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
col = {n: i for i, n in enumerate(names)}
dom = np.array(names)[Wt.argmax(1)]
PV = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', PV)
part = lambda s, keys: Wt[:, [col[n] for n in names if n.startswith(f'B_{s}_') and any(k in n for k in keys)]].sum(1)
faces = [tuple(p.vertices) for p in me.polygons]
report = {}
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); worst = {}
    for f in np.arange(f0, f1 + 0.01, STEP):
        bpy.context.scene.frame_set(int(f), subframe=float(f - int(f)))
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
        P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
        for s in ('L', 'R'):
            own = part(s, ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')) > 0.2
            fl = [fc for fc in faces if PV[fc[0]] == 0 and not any(own[i] for i in fc)]
            fs = [fc for fc in faces if PV[fc[0]] != 0 and not any(own[i] for i in fc)]
            tree = BVHTree.FromPolygons([tuple(p) for p in P], fl); shell = BVHTree.FromPolygons([tuple(p) for p in P], fs)
            for k, mask in ((f'{s}_forearm', (part(s, ('Forearm',)) > 0.5) & (PV == 0)),
                            (f'{s}_hand', (part(s, ('Hand',)) > 0.5) & (PV == 0))):
                d, who, n_close = 0.0, None, 0
                for p in P[mask]:
                    loc, nrm, idx, dist = tree.find_nearest(Vector(p), 0.15)
                    if loc is not None and dist > d and (Vector(p) - loc).dot(nrm) < -0.7 * dist:
                        d = dist; who = str(dom[fl[idx][0]])
                    if shell.find_nearest(Vector(p), 0.005)[0] is not None:
                        n_close += 1
                if d > worst.get(k, (0,))[0]:
                    worst[k] = (d, float(f), who)
                if n_close > worst.get(k + '_mane', (0,))[0]:
                    worst[k + '_mane'] = (n_close, float(f))
    report[an] = {k: ((round(v[0] * 100, 1),) if not k.endswith('_mane') else (v[0],)) + tuple(v[1:]) for k, v in worst.items()}
    print('G6', an, report[an])
json.dump(report, open(os.path.join(HERE, 'work', 'g6_claws.json'), 'w'), indent=1)
