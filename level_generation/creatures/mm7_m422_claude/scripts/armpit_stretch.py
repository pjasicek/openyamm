"""Armpit / side / chest panel stretch of the coat top per clip (half frames): edges of garment 1 (coat top and
sleeves) whose both rest vertices lie in the box |x| 0.06-0.30 m, z 1.00-1.42 m (chest beside the strip, armpit, side
panel and the sleeve root), per side; p99 / max edge ratio and the worst frame; plus the highest wrist (the raised-arm
frame). Args: -- <blend> <tag> [clip ...]   writes review/armpit_<tag>.json"""
import bpy, sys, os, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
blend, tag, clips = a[0], a[1], a[2:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
gv = np.array([x.value for x in me.attributes['garment'].data]); rest = np.array([v.co[:] for v in me.vertices])
E = np.array([tuple(e.vertices) for e in me.edges])
box = lambda P: (np.abs(P[:, 0]) > 0.06) & (np.abs(P[:, 0]) < 0.30) & (P[:, 2] > 1.00) & (P[:, 2] < 1.42)
inb = box(rest)
sel = {s: E[(gv[E[:, 0]] == 1) & (gv[E[:, 1]] == 1) & inb[E[:, 0]] & inb[E[:, 1]] & (np.sign(rest[E[:, 0], 0]) == (1 if s == 'L' else -1))] for s in 'LR'}
RL = {s: np.linalg.norm(rest[e[:, 0]] - rest[e[:, 1]], axis=1) for s, e in sel.items()}
clips = clips or [x for x in ('Standing', 'Walking', 'Attack', 'Hit', 'Death', 'Fidget') if x in bpy.data.actions]
res = {}
for cl in clips:
    act = bpy.data.actions[cl]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; w = {}
    for f in np.arange(f0, f1 + 1e-6, 0.5):
        sc.frame_set(int(f), subframe=float(f - int(f)))
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = np.array([(body.matrix_world @ v.co)[:] for v in m.vertices]); ev.to_mesh_clear()
        for s, e in sel.items():
            r = np.linalg.norm(P[e[:, 0]] - P[e[:, 1]], axis=1) / RL[s]
            for k, v in ((f'{s}_p99', np.percentile(r, 99)), (f'{s}_max', r.max())):
                if k not in w or v > w[k][0]:
                    w[k] = (round(float(v), 3), float(f))
        for s in 'LR':
            z = (rig.matrix_world @ rig.pose.bones[f'B_{s}_Hand'].head).z
            if f'{s}_wrist_z' not in w or z > w[f'{s}_wrist_z'][0]:
                w[f'{s}_wrist_z'] = (round(float(z), 3), float(f))
    res[cl] = w
    print('ARMPIT', cl.ljust(9), ' '.join(f'{k}={v[0]}@{v[1]:.1f}' for k, v in w.items()))
json.dump(res, open(os.path.join(HERE, 'review', f'armpit_{tag}.json'), 'w'), indent=1)
