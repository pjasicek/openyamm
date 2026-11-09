"""G6 for hvf's hands (pf4: forearm/hand skin against the skirt, belt and bodice) against the open shells around the hips (user review 2026-10-22: "hands buried inside body"):
on every frame of every clip, the hands (hand shells, cfg hands) and forearms (sleeve and skin vertices with that
side's forearm/hand weight > 0.5) against the coat-dress (garments 1, 2, minus that arm's own sleeve: arm weight
> 0.3), the sash tail (8), the bag with its strap and clips (cfg bag_pieces, garment 6) and the trouser legs (15).
Open shells: proximity only (nearest surface point), a vertex nearer than CONTACT counts as a contact; the hand of a
shell's inside counts the same as its outside. Prints per clip and side the frames with contacts, the worst depth
(smallest distance) and the target; writes review/g6_hands_<tag>.json. Args: -- <blend> <tag> [clip ...]"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
a = sys.argv[sys.argv.index('--') + 1:]
blend, tag, clips = a[0], a[1], a[2:]
CONTACT = float(os.environ.get('CONTACT', '0.01'))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
gv = np.array([x.value for x in me.attributes['garment'].data]); pv = np.array([x.value for x in me.attributes['piece'].data])
names = [g.name for g in body.vertex_groups]
W = np.zeros((len(me.vertices), len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
gi = {n: i for i, n in enumerate(names)}
arm = {s: W[:, [gi[n] for n in names if n.startswith(f'B_{s}_') and any(t in n for t in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]].sum(1) for s in 'LR'}
fore = {s: W[:, [gi[n] for n in names if n.startswith(f'B_{s}_') and any(t in n for t in ('Forearm', 'Hand', 'Finger'))]].sum(1) for s in 'LR'}
if cfg.C.get('arm_select'):                         # pf4: hands, arms and bodice are one skin shell
    src = {s: np.where((fore[s] > 0.5) & (gv == 0))[0] for s in 'LR'}
    targets = {s: {'skirt': gv == 2, 'belt': gv == 7, 'bodice': (gv == 0) & (arm['L'] + arm['R'] <= 0.3)
                   & (pv != cfg.C['head_whole_pieces'][0])} for s in 'LR'}
else:
    BAG = set(cfg.C.get('bag_pieces', [5, 22, 26]))
    src = {s: np.where((pv == cfg.HANDS[s]) | ((fore[s] > 0.5) & np.isin(gv, (0, 1))))[0] for s in 'LR'}
    targets = {s: {'coat': np.isin(gv, (1, 2)) & (arm[s] <= 0.3), 'sash': gv == 8, 'bag': np.isin(pv, list(BAG)) | (gv == 6),
                   'legs': gv == 15} for s in 'LR'}
polys = [tuple(p.vertices) for p in me.polygons]
tri_of = {s: {k: [p for p in polys if all(m[i] for i in p)] for k, m in targets[s].items()} for s in 'LR'}
acts = [x for x in bpy.data.actions if (not clips or x.name in clips) and x.name in ('Standing', 'Walking', 'Hit', 'Death', 'Fidget', 'Dead')]
report = {}
for act in acts:
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    rep = {s: {'contact_frames': [], 'min_mm': 1e9, 'target': None, 'frame': None} for s in 'LR'}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m2 = ev.to_mesh()
        P = [v.co.copy() for v in m2.vertices]; ev.to_mesh_clear()
        for s in 'LR':
            hit = False
            for k, faces in tri_of[s].items():
                if not faces:
                    continue
                tree = BVHTree.FromPolygons(P, faces)
                for i in src[s]:
                    loc, n, idx, d = tree.find_nearest(P[i], 0.05)
                    if loc is None:
                        continue
                    if d < rep[s]['min_mm'] / 1000:
                        rep[s].update(min_mm=round(d * 1000, 1), target=k, frame=f)
                    if d < CONTACT:
                        hit = True
            if hit:
                rep[s]['contact_frames'].append(f)
    for s in 'LR':
        cf = rep[s]['contact_frames']
        rep[s]['contact_frames'] = f'{len(cf)}/{f1 - f0 + 1}'
        if rep[s]['min_mm'] > 1e8:
            rep[s]['min_mm'] = None
    report[act.name] = rep
    print('G6HANDS', act.name, json.dumps(rep))
json.dump(report, open(os.path.join(HERE, 'review', f'g6_hands_{tag}.json'), 'w'), indent=1)
