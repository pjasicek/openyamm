"""Proportion correction: clear civilian hands from tunic/legs and seat contacting surfaces on the floor."""
from pathlib import Path
import bpy,json,math,sys,runpy
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/timed_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
report={}
forward=rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((0,-1,0))
for name in ('Standing','Walking','Hit','Fidget','Death','Dead'):
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 poses=[];dzs=[]
 for f in range(int(act.frame_range[1])+1):
  scene.frame_set(f)
  # Source shoulder width differs from this peasant; constant small abduction clears his clothing.
  # One-shot endpoints start at the same corrected stance and fade the correction with their stance blend.
  if name=='Walking':degrees=8.0
  elif name in ('Standing','Fidget'):degrees=4.0
  elif name=='Hit':degrees=4.0*max(0,1-min(f,15-f)/4)
  elif name=='Death':degrees=4.0*max(0,1-f/7.5)
  else:degrees=0.0
  axis=(rig.pose.bones['B_Spine2'].matrix.to_3x3()@forward).normalized()
  for side,sign in [('L',1),('R',-1)]:
   pb=rig.pose.bones[f'B_{side}_UpperArm'];m=pb.matrix.copy();t=m.translation.copy()
   m=Matrix.Rotation(math.radians(degrees*sign),4,axis)@m;m.translation=t;pb.matrix=m
   bpy.context.view_layer.update()
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  floor=min((body.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
  dz=max(0.001-floor,0.0)
  pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z+=dz;pb.matrix=m
  bpy.context.view_layer.update()
  poses.append({pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in rig.pose.bones});dzs.append(dz)
 for f,pose in enumerate(poses):
  for n,(q,l) in pose.items():
   pb=rig.pose.bones[n];pb.rotation_quaternion=q
   if n.endswith('UpperArm'):pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':pb.location=l;pb.keyframe_insert('location',frame=f)
 report[name]={'arm_abduction_degrees':8 if name=='Walking' else 4 if name in ('Standing','Fidget') else 'endpoint only','max_floor_lift_m':max(dzs)}
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
(P/'work/clearance_corrections.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/clearance_v1.blend'))
sys.argv=['g6_contacts.py','--',str(P/'work/clearance_v1.blend'),'Standing','Walking','Hit','Fidget','Death']
runpy.run_path(str(P/'scripts/g6_contacts.py'),run_name='__main__')
