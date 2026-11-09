"""Check the actual v6 master under the engine's frozen outgoing-pose crossfade."""
import bpy,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'review/motion_v6'
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_cdr1.blend'))
sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
for track in rig.animation_data.nla_tracks:track.mute=True
bones=list(rig.pose.bones)
def sample(clip,t):
 rig.animation_data.action=bpy.data.actions[clip];f=t*48;sc.frame_set(int(f),subframe=f%1)
 return [(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy()) for b in bones]
def surface():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 result=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();return result
entry=sample('Attack',0);neutral=sample('Standing',0)
assert max((x[0]-y[0]).length+(x[1]-y[1]).magnitude+(x[2]-y[2]).length for x,y in zip(entry,neutral))<1e-6
max_wing=[0,0]
for t in np.linspace(0,1,193):
 sample('Attack',float(t))
 for i,n in enumerate(('LWing1','LWing2')):max_wing[i]=max(max_wing[i],rig.pose.bones[n].rotation_quaternion.angle)
assert max_wing[0]<.82 and max_wing[1]<.50,max_wing
minimum=1e6;max_step=0;count=0
for clip in ('Standing','Walking'):
 for phase in np.linspace(0,.75,12,endpoint=False):
  outgoing=sample(clip,float(phase));previous=None
  for t in np.linspace(0,.125,17):
   incoming=sample('Attack',float(t));rig.animation_data.action=None
   u=t/.125;weight=u*u*(3-2*u)
   for b,a,z in zip(bones,outgoing,incoming):
    b.location=a[0].lerp(z[0],weight);b.rotation_quaternion=a[1].slerp(z[1],weight);b.scale=a[2].lerp(z[2],weight)
   bpy.context.view_layer.update();minimum=min(minimum,surface());count+=1
   quats=[b.rotation_quaternion.copy() for b in bones]
   if previous:max_step=max(max_step,max(2*math.acos(min(1,abs(a.dot(b)))) for a,b in zip(previous,quats)))
   previous=quats
assert minimum>0,minimum
assert math.degrees(max_step)<15,math.degrees(max_step)
sample('Attack',0);q0=rig.pose.bones['Head'].matrix.to_quaternion()
sample('Attack',.125);q1=rig.pose.bones['Head'].matrix.to_quaternion()
head_change=math.degrees(2*math.acos(min(1,abs(q0.dot(q1)))))
assert head_change>20,head_change
report={'entry_matches_standing_frame_0':True,'max_wing_joint_degrees':list(map(math.degrees,max_wing)),
 'simulated_transitions':24,'sampled_blend_poses':count,'min_z_m':minimum,'max_local_bone_step_degrees':math.degrees(max_step),
 'head_orientation_change_at_blend_end_degrees':head_change,'note':'Frozen outgoing local pose, eased .125s crossfade to advancing Attack, matching ModelInstanceSystem. Visual review is separate.'}
(OUT/'entry_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
