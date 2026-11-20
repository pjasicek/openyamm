import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_drape_contacts.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
for role in ['Walking','Death']:
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];keys=[]
 for f in range(int(act.frame_range[1])+1):
  scene.frame_set(f);pb=rig.pose.bones['B_L_UpperArm'];M=pb.matrix.copy()
  t=f/scene.render.fps;blend=max(0,min(1,(t-.1)/.4));blend=blend*blend*(3-2*blend)
  angle=math.radians(9 if role=='Walking' else 32*blend)
  pelvis=rig.pose.bones['B_Pelvis'].matrix.to_3x3()@rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
  axis=pelvis@Vector((0,-1,0));R=Quaternion(axis,angle).to_matrix();N=(R@M.to_3x3()).to_4x4();N.translation=M.translation
  pb.matrix=N;bpy.context.view_layer.update()
  if role=='Death':
   body=bpy.data.objects['Body'];ids=[v.index for v in body.data.vertices if sum(g.weight for g in v.groups if body.vertex_groups[g.group].name.startswith('B_L_') and any(k in body.vertex_groups[g.group].name for k in ['UpperArm','Forearm','Hand','Finger']))>.2]
   for attempt in range(3):
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();low=min(em.vertices[i].co.z for i in ids);ev.to_mesh_clear()
    if low>=.006:break
    direction=rig.pose.bones['B_L_Hand'].head-pb.head;desired=direction+Vector((0,0,.010-low));swing=direction.rotation_difference(desired).to_matrix();N=(swing@pb.matrix.to_3x3()).to_4x4();N.translation=pb.head.copy();pb.matrix=N;bpy.context.view_layer.update()
  keys.append((f,N))
 for f,M in keys:
  scene.frame_set(f);pb=rig.pose.bones['B_L_UpperArm'];pb.matrix=M;pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
act=bpy.data.actions['Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];keys=[]
for f in range(int(act.frame_range[1])+1):
 scene.frame_set(f);pb=rig.pose.bones['B_R_UpperArm'];M=pb.matrix.copy();blend=max(0,min(1,(f/120-.1)/.4));blend=blend*blend*(3-2*blend)
 delta=rig.pose.bones['B_Pelvis'].matrix.to_3x3()@rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();axis=delta@Vector((0,-1,0));R=Quaternion(axis,math.radians(-22*blend)).to_matrix();N=(R@M.to_3x3()).to_4x4();N.translation=M.translation;keys.append((f,N))
for f,M in keys:
 scene.frame_set(f);pb=rig.pose.bones['B_R_UpperArm'];pb.matrix=M;pb.keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_arm_clear.blend'))
