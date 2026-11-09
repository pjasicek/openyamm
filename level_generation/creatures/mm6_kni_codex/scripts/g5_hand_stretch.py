"""G5 hand gate (missing until gob2 review 1): edge stretch on the hands and fingers per frame. Edges whose vertices
carry hand/finger weight > 0.3; per side and action the max posed/rest length ratio, the count of edges > 1.5x, and
for the worst edge its two vertices' finger labels and their top weights (to locate the fault).
Args: -- <blend> action[:frame] [...]   (no frame: every 2nd frame of the action)"""
import bpy, sys, os, json
from pathlib import Path
REPORT={}
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
names = {g.index: g.name for g in body.vertex_groups}
nv = len(me.vertices)
rest = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
hw = np.zeros(nv); side = np.zeros(nv, int); top = []
for v in me.vertices:
    w = sum(e.weight for e in v.groups if 'Hand' in names[e.group] or 'Finger' in names[e.group])
    hw[v.index] = w
    top.append(sorted(((round(e.weight, 2), names[e.group]) for e in v.groups), reverse=True)[:3])
lab = np.zeros(nv, np.int32)
if 'finger' in me.attributes:
    me.attributes['finger'].data.foreach_get('value', lab)
E = np.array([tuple(e.vertices) for e in me.edges])
E = E[(hw[E[:, 0]] > 0.3) & (hw[E[:, 1]] > 0.3)]
rl = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
sd = np.where(rest[E[:, 0], 0] < 0, 'R', 'L')


def posed():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    c = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear(); return c


for pk in a[1:]:
    an, fr = (pk.split(':') + [None])[:2]
    act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    frames = [int(fr)] if fr is not None else list(range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 1))
    worst = {'R': (0, None, None), 'L': (0, None, None)}; cnt = {'R': 0, 'L': 0}
    for f in frames:
        bpy.context.scene.frame_set(f); P = posed()
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(rl, 1e-6)
        for s in 'RL':
            m = sd == s
            cnt[s] = max(cnt[s], int((r[m] > 1.5).sum()))
            i = np.argmax(np.where(m, r, 0))
            if r[i] > worst[s][0]:
                worst[s] = (float(r[i]), f, tuple(E[i]))
    for s in 'RL':
        w, f, e = worst[s]
        info = '' if e is None else ' | '.join(f'v{v} lab {lab[v]} {top[v]}' for v in e)
        print(f'HANDSTRETCH {an:9s} {s}: max {w:.2f}x at frame {f}, edges > 1.5x (worst frame) {cnt[s]} | {info}')

    REPORT[an]={s:{'max_edge_stretch':worst[s][0],'frame':worst[s][1]} for s in 'RL'}
Path(__file__).resolve().parents[1].joinpath('work/g5_final.json').write_text(json.dumps(REPORT,indent=2))
