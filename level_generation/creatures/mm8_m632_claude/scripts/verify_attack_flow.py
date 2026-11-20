"""Verify that old viewer frames 44–60 run at 2.5x without changing their pose path."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def other_clips():
 out={}
 for a in bpy.data.actions:
  if a.name=='Attack':continue
  data=[(fc.data_path,fc.array_index,[tuple(k.co) for k in fc.keyframe_points]) for l in a.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]
  out[a.name]=hashlib.sha256(json.dumps(data).encode()).hexdigest()
 return out
def select():
 sc=bpy.context.scene;assert sc.render.fps==120
 rig=bpy.data.objects['Rig'];a=bpy.data.actions['Attack']
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 return sc,rig,a
def pose(sc,rig,t):
 frame=t*120;sc.frame_set(int(frame),subframe=frame%1)
 return np.array([list(row) for b in rig.pose.bones for row in b.matrix])
start=44/48;old_release=60/48;speed=2.5;new_release=start+(old_release-start)/speed
saved=old_release-new_release
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_fast_aim/textured_uv.blend'))
sc,rig,a=select();assert abs(a.frame_range[1]/120-1.75)<1e-6
other=other_clips();times=np.unique(np.r_[np.arange(0,1.75,1/240),start,old_release,1.75])
expected=[pose(sc,rig,t) for t in times]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
sc,rig,a=select();assert abs(a.frame_range[1]/120-1.55)<1e-6
assert other_clips()==other,'An unrelated animation changed'
error=0
for t,ref in zip(times,expected):
 mapped=t if t<=start else start+(t-start)/speed if t<=old_release else t-saved
 error=max(error,float(np.max(np.abs(pose(sc,rig,mapped)-ref))))
assert error<1e-5,('Retiming changed poses',error)
runtime_speed=speed*new_release/1.25
assert runtime_speed>=2
out={'source_revision':'m632_v4_faster_windup','old_viewer_segment_frames':[44,60],'new_viewer_segment_frames':[44,new_release*48],'viewer_speed_multiplier':speed,'runtime_speed_multiplier':runtime_speed,'native_gameplay_event_s':1.25,'clip_release_s':new_release,'clip_duration_s':1.55,'followthrough_s':.5,'pose_samples':len(times),'max_bone_matrix_error':error,'seven_other_clips_unchanged':other}
d=P/'review/fast_aim';d.mkdir(parents=True,exist_ok=True);(d/'timing_check.json').write_text(json.dumps(out,indent=2)+'\n')
print('FAST AIM', {k:v for k,v in out.items() if k!='seven_other_clips_unchanged'},flush=True)
