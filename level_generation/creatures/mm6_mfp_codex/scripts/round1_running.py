"""Use the normal run library arms over the previously planted native-size gait."""
import bpy,sys,runpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];source=P/'work/round1/normal_run.blend'
if not source.exists():
 sys.argv=['retarget.py','--',str(P/'work/rig_v1.blend'),str(source),str(P.parents[2]/'anim_library/humanoid_set/Unarmed.glb')+':UnarmedRunForward2:NormalRunSource'];runpy.run_path(str(P/'scripts/retarget.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(source));r=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['NormalRunSource'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];names=[f'B_{s}_{n}'for s in 'LR'for n in ['Clavicle','UpperArm','Forearm','Hand']];rows=[]
for f in np.linspace(float(a.frame_range[0]),float(a.frame_range[1]),41):
 sc.frame_set(int(f),subframe=f%1);rows.append({n:r.pose.bones[n].rotation_quaternion.copy()for n in names})
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Running'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];end=float(a.frame_range[1])
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in list(bag.fcurves):
     if any(fc.data_path==f'pose.bones["{n}"].rotation_quaternion'for n in names):bag.fcurves.remove(fc)
 for f,row in zip(np.linspace(0,end,len(rows)),rows):
  for n,q in row.items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
 a.use_fake_user=True;bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'))
