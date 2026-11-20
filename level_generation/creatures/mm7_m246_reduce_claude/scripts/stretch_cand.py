"""Edge stretch (posed / rest length) per source region for the source Body and every ladder candidate in a ladder
blend, over every 4th frame of every clip: the quick form of the hair/strip (g4_skirt.py) and arm (g4_weights.py) gates
before a full build. Candidate faces take the region of the nearest source face centre (rest pose).
Usage: blender -b -P stretch_cand.py -- <ladder blend> <groups .npy>"""
import os, sys, bpy, numpy as np
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, gpath = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; src = bpy.data.objects['Body']
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); g = np.load(os.path.join(HERE, gpath))
A = np.load(os.path.join(HERE, 'work', 'vattrs.npz')); gar = A['garment'][d['faces'][:, 0]]
# report regions: hair, crest, pauldron+plates, arms skin (upper arm + forearm skin), rest
lab = np.where(gar == 3, 1, np.where((gar == 1) & (g == 2), 2, np.where((gar == 6) | (gar == 7), 5, np.where(gar == 2, 9, 0))))
_cen = d['verts'][d['faces']].mean(1); tree = KDTree(len(_cen))
for _i, _c in enumerate(_cen):
    tree.insert(_c, _i)
tree.balance()
nearest = lambda pts: np.array([tree.find(p)[1] for p in pts])
NAMES = {0: 'skin/other', 1: 'hair', 2: 'crest', 5: 'plates+pauldron', 9: 'hip panels'}
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
sc.frame_set(0)
objs = [src] + sorted((o for o in bpy.data.objects if o.name.startswith('Cand_')), key=lambda o: o.name)


def co(o):
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    c = np.array([tuple(o.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear(); return c


setup = {}
for o in objs:
    me = o.data; E = np.array([tuple(e.vertices) for e in me.edges]); P = co(o)
    # edge label = label of the nearest source face to the edge midpoint
    el = lab[nearest((P[E[:, 0]] + P[E[:, 1]]) / 2)]
    setup[o.name] = (E, np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1), el, (P[E[:, 0]] + P[E[:, 1]]) / 2)
res = {o.name: {} for o in objs}
for act in bpy.data.actions:
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1, 4):
        sc.frame_set(f)
        for o in objs:
            E, rl, el, mid = setup[o.name]; P = co(o)
            st = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(rl, 1e-6)
            for k in NAMES:
                m = el == k
                if m.any():
                    cur = res[o.name].get(k, (0, ''))
                    if st[m].max() > cur[0]:
                        j = np.flatnonzero(m)[st[m].argmax()]
                        res[o.name][k] = (float(st[m].max()), f'{act.name}:{f} at ' + ','.join(f'{x:.3f}' for x in mid[j]))
for o in objs:
    print('STRETCH', o.name, ' | '.join(f'{NAMES[k]} {v[0]:.2f} {v[1]}' for k, v in sorted(res[o.name].items())), flush=True)
