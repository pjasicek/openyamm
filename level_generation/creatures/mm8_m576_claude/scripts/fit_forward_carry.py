"""Add mesh-measured clearance for the forward carry without changing the fixed grip."""
import bpy,sys,math,runpy,json
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
base=P/'work/lunge_before_carry_clearance.blend'
if not base.exists():
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_textured_uv.blend'));bpy.ops.wm.save_as_mainfile(filepath=str(base))
else:bpy.ops.wm.open_mainfile(filepath=str(base))
sc=bpy.context.scene;rig=bpy.data.objects['Rig'];names=[b.name for b in rig.data.bones]
def act(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
act(bpy.data.actions['Standing']);sc.frame_set(0);carry={n:armik.W(rig,n).to_3x3().normalized().copy() for n in ('B_L_Clavicle','B_L_UpperArm','B_L_Forearm','B_L_Hand')}
written={}
for name,side,degrees in [('Attack','R',2.0),('Hit','L',-7.0),('Running','L',-7.0),('Death','L',-4.0)]:
 a=bpy.data.actions[name];end=float(a.frame_range[1]);frames=np.arange(0,end+.001,.25);rows=[]
 for f in frames:
  act(a);sc.frame_set(int(f),subframe=float(f%1));rows.append({n:rig.pose.bones[n].matrix_basis.copy() for n in names})
 for i,(f,row) in enumerate(zip(frames,rows)):
  act(None)
  for n,m in row.items():rig.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update()
  if name=='Hit':
   # Stabilize the polearm as the torso flinches; chest-relative carry drives the long tines into the foot.
   for n,R in carry.items():armik.set_world(rig,n,armik.rot_world(armik.W(rig,n),R))
  w=math.exp(-.5*((f/30-.55)/.28)**2) if name=='Death' else 1.
  n=f'B_{side}_UpperArm';M=armik.W(rig,n);R=Matrix.Rotation(math.radians(degrees)*w,3,'Y')@M.to_3x3();armik.set_world(rig,n,armik.rot_world(M,R));rows[i]={n:rig.pose.bones[n].matrix_basis.copy() for n in names}
 bpy.data.actions.remove(a);a=bpy.data.actions.new(name);a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=end;act(a);prev={}
 for f,row in zip(frames,rows):
  for n,m in row.items():
   q=m.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f))
   if n=='B_Pelvis':pb.location=m.translation;pb.keyframe_insert('location',frame=float(f))
 written[name]=end/30
code=(P/'scripts/attack_cannibal.py').read_text();exec(code[code.index('FA=.6;UA=.5;'):code.index('act(None);bpy.ops.wm.save_as_mainfile')])
act(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_textured_uv.blend'))
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/quick_rig_probe.py'),run_name='__main__')
