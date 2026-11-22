"""Find stretched edges in a clip frame: edges posed longer than STRETCH x their rest length, with the dominant
groups of their vertices. Usage: stretch_probe.py <action> <frame>"""
import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Dillo_Rig']; ob = bpy.data.objects['Dillo']; me = ob.data
rest = np.array([v.co[:] for v in me.vertices])
act = bpy.data.actions[a[0]]; rig.animation_data.action = act
if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[1]))
dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg); em = ev.to_mesh()
pos = np.array([v.co[:] for v in em.vertices]); ev.to_mesh_clear()
E = np.array([e.vertices[:] for e in me.edges])
lr = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1); lp = np.linalg.norm(pos[E[:, 0]] - pos[E[:, 1]], axis=1)
ratio = lp / np.maximum(lr, 1e-6)
names = [g.name for g in ob.vertex_groups]
part = np.zeros(len(rest), int)
for p in me.polygons:
    for v in p.vertices: part[v] = me.attributes['part'].data[p.index].value
for i in np.argsort(-ratio)[:12]:
    va, vb = E[i]
    ga = sorted(((names[g.group], round(g.weight, 2)) for g in me.vertices[va].groups), key=lambda x: -x[1])[:3]
    gb = sorted(((names[g.group], round(g.weight, 2)) for g in me.vertices[vb].groups), key=lambda x: -x[1])[:3]
    print('EDGE ratio %.1f len %.3f' % (ratio[i], lp[i]), 'part', part[va], np.round(rest[va], 3).tolist(), ga, '|', np.round(rest[vb], 3).tolist(), gb)
