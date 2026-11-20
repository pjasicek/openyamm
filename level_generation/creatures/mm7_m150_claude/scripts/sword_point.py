"""Where a sword sample sits at a clip time (world position, nearest body vertex's dominant bone). Args: -- <blend> clip frame t"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
act = bpy.data.actions[a[1]]; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
f = float(a[2]); bpy.context.scene.frame_set(int(f), subframe=f - int(f))
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
hm = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
c = hm @ Vector(G['handle_centre_hand_local']); ax = (hm.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
p = c + ax * float(a[3])
deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
i = int(np.argmin(np.linalg.norm(P - np.array(p), axis=1)))
v = body.data.vertices[i]; g = max(v.groups, key=lambda e: e.weight)
print('SWORDPT', a[1], f, 'point', [round(x, 3) for x in p], 'nearest vertex', i, 'bone', body.vertex_groups[g.group].name, 'piece', body.data.attributes['piece'].data[i].value)
