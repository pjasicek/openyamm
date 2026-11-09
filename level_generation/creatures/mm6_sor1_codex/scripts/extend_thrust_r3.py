"""Extend the arms during the final staff drive; retain the solved opposing hand orientations."""
import bpy,sys,json,runpy
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));bpy.ops.wm.open_mainfile(filepath=str(p/'work/round3_motion_before_extension.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
import arm_solver as sol
sides={s:sol.Side('B_'+s+'_') for s in 'LR'};L=json.loads((p/'work/round2_left_grip.json').read_text());sides['L'].grip_hand=Vector(L['centre']);sides['L'].axis_hand=Vector(L['axis'])
act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];names=[b.name for b in rig.pose.bones];poses=[]
for f in range(301):
 scene.frame_set(f);poses.append({n:rig.pose.bones[n].matrix_basis.copy() for n in names})
rig.animation_data.action=None;keys=[];miss=0
changed=[n for n in names if any(n.startswith('B_'+s+'_'+b) for s in 'LR' for b in ['UpperArm','Forearm','Hand'])]
def smooth(x):
 x=max(0,min(1,x));return x*x*x*(10+x*(-15+6*x))
for f,d in enumerate(poses):
 for n,m in d.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update();t=f/120;offset=Vector((0,-.12*smooth((t-1)/.45)*smooth((2-t)/.32),0))
 if offset.length>1e-9:
  for sd in 'RL':
   side=sides[sd];H=rig.pose.bones[side.s+'Hand'].matrix.copy();S=rig.pose.bones[side.s+'UpperArm'].head.copy();P=rig.pose.bones[side.s+'Forearm'].head-S;G=H@side.grip_hand+offset;r=side.pose_anatomical(G,H.to_3x3(),P);miss=max(miss,r['miss']);side.apply(r)
 keys.append({n:(rig.pose.bones[n].location[:],rig.pose.bones[n].rotation_quaternion[:],rig.pose.bones[n].scale[:]) for n in changed})
assert miss<.0002,miss
rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
for f,d in enumerate(keys):
 for n,(loc,rot,scale) in d.items():
  pb=rig.pose.bones[n];pb.location=loc;pb.rotation_quaternion=rot;pb.scale=scale
  for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=f,group=n)
runpy.run_path(str(p/'scripts/normalize_keys_r2.py'));bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round3_extension_candidate.blend'))
(p/'work/round3_extension_keys.json').write_text(json.dumps(keys));print('EXTENSION',miss,flush=True)
