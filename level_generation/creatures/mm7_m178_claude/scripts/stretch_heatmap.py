"""Posed mesh coloured by edge stretch (max posed/rest edge length at each vertex: white 1.0 -> red 2.0+, blue < 0.7)
at one action frame; front/back/three-quarter + close-ups of both shoulders. Args: -- <blend> <action> <frame> <out>"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, action, frame, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rest = np.array([tuple(v.co) for v in me.vertices])
act = bpy.data.actions[action]; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(frame))
deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
E = np.array([tuple(e.vertices) for e in me.edges])
r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1), 1e-6)
vs = np.ones(len(rest)); vmin = np.ones(len(rest))
np.maximum.at(vs, E[:, 0], r); np.maximum.at(vs, E[:, 1], r)
np.minimum.at(vmin, E[:, 0], r); np.minimum.at(vmin, E[:, 1], r)
attr = me.color_attributes.new('stretch', 'FLOAT_COLOR', 'POINT')
for i in range(len(rest)):
    t = min(1.0, max(0.0, (vs[i] - 1.6) / 1.4))           # only real stretch: white < 1.6x, red >= 3x
    c = (1.0, 1.0 - t, 1.0 - t, 1.0) if vmin[i] > 0.5 else (0.3, 0.4, 1.0, 1.0)
    attr.data[i].color = c
scene = bpy.context.scene; common.workbench_clay(scene)
scene.display.shading.color_type = 'VERTEX'; me.color_attributes.active_color = attr
common.render_views(out, 0.95, 1.9, views=('front', 'back', 'three_quarter'), resolution=(500, 560), target=(0, -0.6))
for s, x in (('R', -0.2), ('L', 0.2)):
    common.render_views(f'{out}_{s}sh', 1.3, 0.5, views=('front', 'back'), resolution=(400, 400), target=(x, -0.6))
