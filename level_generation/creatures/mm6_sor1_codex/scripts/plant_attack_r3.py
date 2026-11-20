"""Give the rear leg reach during weight transfer, preserving all arm rotations and the accepted Cast."""
import bpy,sys,math,ast,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/round3_motion_pre_plant.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
node=next(n for n in ast.parse((p/'scripts/round2_motion.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='leg');exec(compile(ast.Module(body=[node],type_ignores=[]),'round2_motion.py','exec'))
act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];names=[b.name for b in rig.pose.bones];poses=[];targets=[]
for f in range(301):
 scene.frame_set(f);poses.append({n:rig.pose.bones[n].matrix_basis.copy() for n in names});targets.append({s:rig.pose.bones[f'B_{s}_Foot'].matrix.copy() for s in 'LR'})
rig.animation_data.action=None;robe=[n for n in names if n.startswith('Robe_')];keys=[]
def smooth(x):
 x=max(0,min(1,x));return x*x*x*(10+x*(-15+6*x))
for f,d in enumerate(poses):
 for n,m in d.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update();t=f/120;before={n:rig.pose.bones[n].head.copy() for n in ['B_Pelvis',*[f'B_{s}_{b}' for s in 'LR' for b in ['Calf','Foot']]]};raw={n:rig.pose.bones[n].matrix.copy() for n in robe}
 pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z-=.033*smooth((t-.40)/.50)*smooth((2.4-t)/.50);pb.matrix=m;bpy.context.view_layer.update()
 leg('L',targets[f]['L']);leg('R',targets[0]['R']);after={n:rig.pose.bones[n].head.copy() for n in before}
 for n in robe:
  z=rig.data.bones[n].head_local.z;x=rig.data.bones[n].head_local.x;mix=max(0,min(1,.5+x/.4));dp=after['B_Pelvis']-before['B_Pelvis'];dk=(after['B_R_Calf']-before['B_R_Calf']).lerp(after['B_L_Calf']-before['B_L_Calf'],mix);df=(after['B_R_Foot']-before['B_R_Foot']).lerp(after['B_L_Foot']-before['B_L_Foot'],mix);delta=df.lerp(dk,max(0,min(1,(z-.10)/.48))) if z<.58 else dk.lerp(dp,max(0,min(1,(z-.58)/.46)));m=raw[n].copy();m.translation+=delta;rig.pose.bones[n].matrix=m;bpy.context.view_layer.update()
 assert (rig.pose.bones['B_R_Foot'].head-targets[0]['R'].translation).length<.0001,(f,'rear foot reach')
 keys.append({n:(pb.location[:],pb.rotation_quaternion[:],pb.scale[:]) for n in ['B_Pelvis',*[f'B_{s}_{b}' for s in 'LR' for b in ['Thigh','Calf','Foot']],*robe] for pb in [rig.pose.bones[n]]})
# Replace only the lower-body channels on each editable LOD; rest surfaces and baked textures are untouched.
for path in ['work/round3_motion.blend',*[f'work/round3_lod{n}.blend' for n in range(4)]]:
 bpy.ops.wm.open_mainfile(filepath=str(p/path));rig=bpy.data.objects['Rig'];act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for f,d in enumerate(keys):
  for n,(loc,rot,scale) in d.items():
   pb=rig.pose.bones[n];pb.location=loc;pb.rotation_quaternion=rot;pb.scale=scale
   for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=f,group=n)
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 bpy.ops.wm.save_as_mainfile(filepath=str(p/path))
(p/'work/round3_plant_correction.json').write_text(json.dumps({'pelvis_lowering_max_mm':33,'envelope_seconds':[.4,.9,1.9,2.4],'unchanged':'all arm rotations, two-hand frames, other seven clips, rest geometry and UVs'},indent=2))
