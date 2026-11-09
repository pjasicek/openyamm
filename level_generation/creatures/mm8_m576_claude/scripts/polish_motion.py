"""Keep the native durations; smooth source hand acceleration and lead the downstroke with the tines."""
import bpy,sys,math,json,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];W=P/'work';sys.path.insert(0,str(P/'scripts'));import armik
base=W/'master_before_final_polish.blend'
if not base.exists():
 bpy.ops.wm.open_mainfile(filepath=str(W/'master_textured_uv.blend'));bpy.ops.wm.save_as_mainfile(filepath=str(base))
else:bpy.ops.wm.open_mainfile(filepath=str(base))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;names=[b.name for b in rig.data.bones];spine=rig.data.bones['B_Spine'];upper={b.name for b in spine.children_recursive}|{'B_Spine'}
def act(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
for name in ('Walking','Running','Hit','Fidget','Death','Attack'):
 a=bpy.data.actions[name];end=float(a.frame_range[1]);frames=np.arange(0,end+.001,.25);saved=[]
 for f in frames:
  act(a);sc.frame_set(int(f),subframe=float(f%1));saved.append({n:rig.pose.bones[n].matrix_basis.copy() for n in names})
 rows=[]
 for i,(f,snap) in enumerate(zip(frames,saved)):
  act(None)
  for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
  if name in ('Running','Hit','Fidget','Death'):
   # 42ms Gaussian filter preserves cadence while removing resampling corners from the source curves.
   for n in upper:
    q0=snap[n].to_quaternion();v=np.zeros(4);total=0
    for k in range(-10,11):
     j=min(len(saved)-1,max(0,i+k));q=saved[j][n].to_quaternion();q=-q if q.dot(q0)<0 else q;weight=math.exp(-.5*(k/5)**2);v+=np.array(q)*weight;total+=weight
    rig.pose.bones[n].rotation_quaternion=Quaternion(v/np.linalg.norm(v))
  bpy.context.view_layer.update()
  if name=='Attack':
   w=math.sin(math.pi*f/48)**2;M=armik.W(rig,'B_L_Hand');pivot=M.translation.copy();M=Matrix.Rotation(math.radians(45)*w,4,'X')@M;M.translation=pivot;armik.set_world(rig,'B_L_Hand',M)
  if name=='Walking':
   # The open hand faces the thigh during the natural arm swing.
   h='B_R_Hand';M=armik.W(rig,h);root=rig.data.bones[h].matrix_local;wr=root.translation;normal=(rig.data.bones['B_R_Finger1'].head_local-wr).cross(rig.data.bones['B_R_Finger4'].head_local-wr).normalized();axis=root.to_3x3().inverted()@normal
   for _ in range(2):
    M=armik.W(rig,h);normal=M.to_3x3()@axis;origin=(M.translation+sum((armik.W(rig,f'B_R_Finger{j}').translation for j in range(5)),Vector())/5)/2;goal=armik.W(rig,'B_R_Thigh').translation-origin;goal.z=0;ang=normal.angle(goal)
    if ang>math.radians(30):
     q=normal.rotation_difference(goal);q=Quaternion(q.axis,ang-math.radians(30));armik.set_world(rig,h,armik.rot_world(M,q.to_matrix()@M.to_3x3()))
  rows.append({n:rig.pose.bones[n].matrix_basis.copy() for n in names})
 bpy.data.actions.remove(a);a=bpy.data.actions.new(name);a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=end;act(a);prev={}
 for f,snap in zip(frames,rows):
  for n,m in snap.items():
   pb=rig.pose.bones[n];q=m.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f))
   if n=='B_Pelvis':pb.location=m.translation;pb.keyframe_insert('location',frame=float(f))
 print('POLISH',name,flush=True)
FA=.6;UA=.5;source=(P/'scripts/twist_bones.py').read_text();exec(source[source.index('def twist_about('):source.index("for act in [a for a in bpy.data.actions if a.use_fake_user]:")])
for a in bpy.data.actions:
 if a.name in ('Walking','Running','Hit','Fidget','Death','Attack'):bake_twist(a)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for key in curve.keyframe_points:key.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(W/'polished_motion.blend'))
sys.argv=['pauldrons.py','--',str(W/'polished_motion.blend'),str(W/'master_textured_uv.blend')];runpy.run_path(str(P/'scripts/pauldrons.py'),run_name='__main__')
sys.argv=['export_runtime.py'];runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
