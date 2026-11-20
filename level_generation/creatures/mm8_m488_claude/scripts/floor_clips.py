"""Place the evaluated sole on the floor; preserve source limb motion and record root corrections."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
src,out,*names=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;report={}
for name in names:
 act=bpy.data.actions[name];rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 f0,f1=map(int,act.frame_range);poses=[];arms=[]
 for f in range(f0,f1+1):
  sc.frame_set(f)
  if name=='Walking':
   rig.animation_data.action=None
   for side,sign in [('L',-1),('R',1)]:
    pb=rig.pose.bones['B_'+side+'_UpperArm'];M=pb.matrix.copy();tr=M.translation.copy();M=Matrix.Rotation(sign*math.radians(6),4,'Y')@M;M.translation=tr;pb.matrix=M;bpy.context.view_layer.update()
   arms.append({s:rig.pose.bones['B_'+s+'_UpperArm'].rotation_quaternion.copy() for s in 'LR'})
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  z=min((body.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
  root=rig.pose.bones['B_Pelvis'];M=root.matrix.copy();M.translation+=Vector((0,0,-z))
  rig.animation_data.action=None;root.matrix=M;bpy.context.view_layer.update();poses.append(root.location.copy());rig.animation_data.action=act
 for i,pos in enumerate(poses):
  root.location=pos;root.keyframe_insert('location',frame=f0+i)
  if arms:
   for side,q in arms[i].items():
    pb=rig.pose.bones['B_'+side+'_UpperArm'];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f0+i)
 report[name]={'frames':len(poses),'root_location_z_range':[min(x.z for x in poses),max(x.z for x in poses)]}
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()))
print('FLOOR',json.dumps(report))
