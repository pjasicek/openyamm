"""Diagnostic: the worst stretched edges of one (action, frame) of work/anim_v3.blend with their vertices' rest
positions, part (0 body / 1 head mesh), piece size and weights. Config work/probe_edges.json {"action", "frame"}."""
import bpy, bmesh, json
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
cfg = json.loads((P / 'work' / 'probe_edges.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v3.blend'))
rig = bpy.data.objects['Rig']; queen = bpy.data.objects['Queen']; me = queen.data
gi = {g.index: g.name for g in queen.vertex_groups}
part = np.zeros(len(me.vertices), int)
pf = [p.value for p in me.attributes['part'].data]
for p in me.polygons:
    if pf[p.index]:
        part[list(p.vertices)] = 1
E = np.array([tuple(e.vertices) for e in me.edges])
rest = np.array([tuple(v.co) for v in me.vertices])
rl = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
act = bpy.data.actions[cfg['action']]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(cfg['frame'])
em = queen.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
pc = np.array([tuple(v.co) for v in em.vertices])
L = np.linalg.norm(pc[E[:, 0]] - pc[E[:, 1]], axis=1)
r = np.where(rl > 0.005, L / np.maximum(rl, 1e-6), 1)
for k in np.argsort(-r)[:6]:
    out = []
    for vi in E[k]:
        v = me.vertices[int(vi)]
        out.append({'v': int(vi), 'co': [round(x, 3) for x in v.co], 'part': int(part[vi]),
                    'w': {gi[g.group]: round(g.weight, 2) for g in v.groups if g.weight > 0.03}})
    print('EDGE', round(float(r[k]), 1), 'rest_mm', round(float(rl[k]) * 1000, 1), json.dumps(out))
