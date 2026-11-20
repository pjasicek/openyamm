"""Close simulated cloth loops without changing source body motion, geometry or UVs."""
import bpy,sys,json
from pathlib import Path
from mathutils import Quaternion
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v9.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene
names=[b.name for b in r.pose.bones if b.name.startswith(('Cloak_','Tabard_','BackTabard_'))]
if not sc.get('cloth_loops_closed'):
 for name in ['Standing','Walking','Running','Fidget']:
  a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
  start,end=map(int,a.frame_range);samples=[]
  for f in range(start,end+1):
   sc.frame_set(f);samples.append({n:(r.pose.bones[n].rotation_quaternion.copy(),r.pose.bones[n].location.copy()) for n in names})
  corrections={n:(samples[0][n][0]@samples[-1][n][0].inverted(),samples[0][n][1]-samples[-1][n][1]) for n in names}
  for f,pose in enumerate(samples):
   sc.frame_set(f);t=f/(len(samples)-1);t=t*t*(3-2*t)
   for n,(rot,loc) in pose.items():
    dq,dl=corrections[n];b=r.pose.bones[n];b.rotation_quaternion=Quaternion().slerp(dq,t)@rot;b.location=loc+dl*t
    b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
  print('CLOSED_CLOTH',name,max(v[1].length for v in corrections.values()),flush=True)
 sc['cloth_loops_closed']=True
 bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v9.blend'))
