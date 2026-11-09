"""Close the clearance-corrected run loop over its last four frames and recheck head clearance."""
from pathlib import Path
import bpy,sys,math,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
from g6_head_clearance import Clearance
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v6.blend'))
rig=bpy.data.objects['Rig'];act=bpy.data.actions['Running'];rig.animation_data.action=act
rig.animation_data.action_slot=act.slots[0];scene=bpy.context.scene
f0,f1=act.frame_range
scene.frame_set(int(f0));start={b.name:b.rotation_quaternion.copy() for b in rig.pose.bones}
scene.frame_set(int(f1));end={b.name:b.rotation_quaternion.copy() for b in rig.pose.bones}
changed={n:start[n]@end[n].inverted() for n in start if start[n].rotation_difference(end[n]).angle>1e-4}
rows=[]
for f in range(int(f1)-4,int(f1)+1):
 scene.frame_set(f);u=(f-(f1-4))/4;u=u*u*(3-2*u)
 rows.append((f,{n:rig.pose.bones[n].rotation_quaternion.slerp(d@rig.pose.bones[n].rotation_quaternion,u) for n,d in changed.items()}))
for f,qs in rows:
 for n,q in qs.items():
  b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f,group=n)
scene.frame_set(int(f1))
assert max(start[n].rotation_difference(rig.pose.bones[n].rotation_quaternion).angle for n in start)<.002
clear=Clearance(bpy.data.objects['Body']);worst=(0,0)
for i in range(int((f1-f0)*2)+1):
 f=f0+i*.5;scene.frame_set(int(f),subframe=f-int(f));d=clear.measure()[0]
 if d>worst[0]:worst=(d,f)
assert worst[0]<.01,worst
report={'changed_bones':list(changed),'blend_frames':[f1-4,f1],'max_head_penetration_m':worst[0],'worst_frame':worst[1]}
(p/'work/run_loop_gate.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v7.blend'));print('RUN_LOOP',report)
