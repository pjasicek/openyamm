import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v6.blend'));r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0);pb=r.pose.bones['Axe'];o=bpy.data.objects['AxeMesh'];G=json.loads((P/'work/grip_pose_R.json').read_text());mh=r.pose.bones['B_R_Hand'].matrix
print('GRIPC',list(mh@Vector(G['handle_centre_hand_local'])),'GRIPA',list(mh.to_3x3()@Vector(G['handle_axis_hand_local'])))
print('AxePB',pb.rotation_mode,list(pb.rotation_quaternion),list(pb.rotation_euler),'mat',pb.matrix,'REST',pb.bone.matrix_local,'deform',pb.bone.use_deform)
print('MESH',o.matrix_world,'RIG',r.matrix_world,'groups',[(g.name,g.index) for g in o.vertex_groups],'mods',[(m.type,m.name) for m in o.modifiers])
m=pb.matrix@pb.bone.matrix_local.inverted();print('DERIVEDC',list(m@Vector((0,0,.88))),'A',list(m.to_3x3()@Vector((0,0,1))))
print('ARM ANGLES',[(n,tuple(r.pose.bones[n].rotation_quaternion)) for n in ['B_R_Hand','B_R_Forearm','B_R_ForearmTwist']])
