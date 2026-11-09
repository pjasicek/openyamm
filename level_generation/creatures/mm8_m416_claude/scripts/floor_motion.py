"""Set contact height from the evaluated feet, keeping the running flight arc and the death's final body contact."""
from pathlib import Path
import bpy,numpy as np,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/levelled.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
vg=[g.name for g in body.vertex_groups]
feet=np.array([sum(e.weight for e in v.groups if any(x in vg[e.group] for x in ('Foot','Toe')))>.5 for v in body.data.vertices])
def act(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
report={}
for a in list(bpy.data.actions):
 if not a.use_fake_user:continue
 n=int(a.frame_range[1])+1;lows=[];loc=[]
 act(a)
 for f in range(n):
  sc.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  z=np.array([(body.matrix_world@v.co).z for v in me.vertices]);ev.to_mesh_clear()
  lows.append(float(z.min() if a.name=='Death' else z[feet].min()))
  loc.append(rig.pose.bones['B_Pelvis'].location.copy())
 lows=np.array(lows)
 if a.name=='Running':dz=np.repeat(-float(lows.min()),n)
 else:
  dz=-np.convolve(np.pad(lows,(1,1),mode='edge'),[.2,.6,.2],mode='valid')
  dz=np.maximum(dz,-lows-.003)
 pb=rig.pose.bones['B_Pelvis'];inv=pb.bone.matrix_local.to_3x3().inverted()
 for f in range(n):
  sc.frame_set(f);pb.location=loc[f]+inv@Vector((0,0,float(dz[f])));pb.keyframe_insert('location',frame=f)
 report[a.name]={'before_cm':[float(lows.min()*100),float(lows.max()*100)],'correction_cm':[float(dz.min()*100),float(dz.max()*100)]}
# A held corpse is exactly the final death frame.
death=bpy.data.actions['Death'];act(death);sc.frame_set(int(death.frame_range[1]))
pose={pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in rig.pose.bones}
old=bpy.data.actions.get('Dead')
if old:bpy.data.actions.remove(old)
a=bpy.data.actions.new('Dead');a.use_fake_user=True;act(a)
for f in (0,1):
 for n,(q,l) in pose.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f)
  if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
act(None);json.dump(report,open(p/'work/floor_report.json','w'),indent=2)
print('FLOOR',json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animated.blend'))
