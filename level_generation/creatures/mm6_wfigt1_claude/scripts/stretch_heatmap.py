"""Edge-stretch heatmap (length ratio to bind, per vertex the max of its edges; blue 1.0 -> red 1.6+) of one clip
frame, clay render front and back. Args: blend clip frame tag"""
import bpy, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, clip, frame, tag = sys.argv[sys.argv.index('--') + 1:][:4]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, blend))
arm = bpy.data.objects['Werewolf_Rig']; mesh = bpy.data.objects['Werewolf']; me = mesh.data
E = np.array([e.vertices[:] for e in me.edges])


def verts():
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear(); return P


arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
P0 = verts()
a = bpy.data.actions[clip]; arm.animation_data.action = a
if a.slots: arm.animation_data.action_slot = a.slots[0]
bpy.context.scene.frame_set(int(frame)); P = verts()
r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1), 1e-6)
vr = np.ones(len(P0))
np.maximum.at(vr, E[:, 0], r); np.maximum.at(vr, E[:, 1], r)
col = me.color_attributes.new('stretch', 'FLOAT_COLOR', 'POINT')
for i, x in enumerate(vr):
    t = min(1.0, max(0.0, (x - 1.0) / 0.6))
    col.data[i].color = (t, 0.2 * (1 - t), 1 - t, 1)
me.color_attributes.active_color = col
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'VERTEX'
hips = arm.matrix_world @ arm.pose.bones['Spine'].head
common.render_views(os.path.join(common.REVIEW, tag), float(hips.z), 1.0, views=('front', 'back', 'left'),
                    resolution=(600, 600), target=(float(hips.x), float(hips.y)))
