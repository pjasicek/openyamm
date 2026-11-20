"""Weight the selected RPG overhead stroke without losing the measured two-hand grip."""
import bpy,sys,os,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/forge_concept_parts.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Forge_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
end=float(a.frame_range[1]);samples=[];duration=2.5
# Preserve the fast contact portion; put the extra time into lifting and recovering the heavy head.
old=np.array([0,.18,.34,.40,.52,.75,1.]);new=np.array([0,.23,.42,.50,.60,.82,1.])
for frame in np.arange(0,duration*30+.001,.5):
 u=float(np.interp(frame/(duration*30),new,old));sf=u*end;sc.frame_set(int(sf),subframe=sf%1)
 pose={b.name:b.matrix_basis.copy() for b in r.pose.bones}
 lean=float(np.interp(u,[0,.15,.28,.36,.46,.58,.76,1],[0,-5,-9,-6,12,15,7,0]))
 w=armik.W(r,'B_Spine');turn=r.pose.bones['B_Spine2'].matrix.to_3x3()@r.data.bones['B_Spine2'].matrix_local.to_3x3().inverted();right=turn@Vector((1,0,0));right.z=0;right.normalize()
 mat=(Quaternion(right,math.radians(lean)).to_matrix()@w.to_3x3()).to_4x4();mat.translation=w.translation;armik.set_world(r,'B_Spine',mat);pose['B_Spine']=r.pose.bones['B_Spine'].matrix_basis.copy();samples.append((float(frame),pose))
r.animation_data.action=None;bpy.data.actions.remove(a);a=bpy.data.actions.new('Forge_Attack');a.use_fake_user=True;r.animation_data.action=a;previous={}
for frame,pose in samples:
 for n,m in pose.items():
  b=r.pose.bones[n];q=m.to_quaternion()
  if n in previous and q.dot(previous[n])<0:q=-q
  previous[n]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('location',frame=frame)
a.use_frame_range=True;a.frame_start=0;a.frame_end=duration*30
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_heavy_attack.blend'))
(P/'review/forge_heavy_attack_selection.json').write_text(json.dumps({'compared':'heavy_maul_sources.json','selected':'RPG 2HandAxeAttack1 (existing fitted overhead strike)','why':'Overhead lift and downward drive; grounded stance with a complete recovery. RPG 4/6 are horizontal sweeps. Meshy 128 turns 80.8 degrees and ends crouched without recovery. Mixamo power slash lunges substantially.','duration_s':duration,'additional_torso_pitch_degrees':[-9,15],'timing_old':old.tolist(),'timing_new':new.tolist(),'impact_s':float(np.interp(.8/(end/30),old,new)*duration),'other_roles_unchanged':True},indent=2)+'\n')
print('HEAVY_STROKE_READY',end/30,'->',duration,flush=True);os._exit(0)
