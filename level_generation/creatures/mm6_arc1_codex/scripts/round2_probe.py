import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round2/baseline/work/rig_equipped.blend'))
r=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
h=r.pose.bones['B_L_Hand'].matrix.copy();g=Matrix(json.loads((P/'work/bow_binding.json').read_text())['hand_local']);print('HAND',list(h.translation),'GRIP_AXIS',list(h.to_3x3()@g.to_3x3().col[2]),'STRING',list(h.to_3x3()@g.to_3x3().col[1]),flush=True)
r.animation_data.action=None
old=h.to_3x3()@g.to_3x3().col[2];z=Vector((.08,-.55,.831)).normalized();R=old.rotation_difference(z).to_matrix()@h.to_3x3();m=R.to_4x4();m.translation=h.translation;r.pose.bones['B_L_Hand'].matrix=m;bpy.context.view_layer.update()
for n,q in json.loads((P/'work/grip_pose.json').read_text())['finger_local'].items():r.pose.bones[n].rotation_quaternion=Quaternion(q)
bpy.context.view_layer.update();r.pose.bones['Bow'].matrix=r.pose.bones['B_L_Hand'].matrix@g;bpy.context.view_layer.update()
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/round2/angled_grip'),.88,2.3,views=('front','left','three_quarter'),resolution=(650,900))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2_probe.blend'))
