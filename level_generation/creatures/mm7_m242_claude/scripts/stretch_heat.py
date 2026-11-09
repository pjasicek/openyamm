"""Edge-stretch heatmap of 'Body' at one clip time: vertex colour = the largest posed/rest length ratio of its edges
(blue 1.0 -> red >= HEAT_MAX), front, three-quarter and back renders around the head and shoulders.
Args: -- <blend> <action> <frame> <out prefix>"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
HM = float(os.environ.get('HEAT_MAX', '3'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
deps = bpy.context.evaluated_depsgraph_get()
def co():
    bpy.context.view_layer.update(); deps.update(); ev = body.evaluated_get(deps); m = ev.to_mesh()
    c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); ev.to_mesh_clear(); return c.reshape(-1, 3)
E = np.array([tuple(e.vertices) for e in me.edges]); R0 = co(); L0 = np.linalg.norm(R0[E[:, 0]] - R0[E[:, 1]], axis=1)
act = bpy.data.actions[a[1]]; rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[2])); C = co()
r = np.linalg.norm(C[E[:, 0]] - C[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)
vr = np.ones(len(C)); np.maximum.at(vr, E[:, 0], r); np.maximum.at(vr, E[:, 1], r)
col = me.color_attributes.new('heat', 'FLOAT_COLOR', 'POINT')
for i, x in enumerate(vr):
    t = min(1.0, max(0.0, (x - 1) / (HM - 1))); col.data[i].color = (t, 0.2 * (1 - t), 1 - t, 1)
me.color_attributes.active_color = col
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
worst = np.argsort(-vr)[:8]
print('HEAT worst vertices', [(int(i), int(pv[i]), round(float(vr[i]), 2), [round(float(x), 2) for x in R0[i]]) for i in worst])
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'VERTEX'
hz = (rig.matrix_world @ rig.pose.bones['B_Head'].head).z
common.render_views(a[3], hz - 0.15, 1.0, views=('front', 'three_quarter', 'back'), resolution=(500, 500))
