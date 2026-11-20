"""Keep the pirate looking forward over the carried weapon, with source reaction motion retained."""
from pathlib import Path
import bpy,sys,math
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/all_motion_clear.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
rest=r.data.bones['B_Head'].matrix_local.to_3x3().inverted()@Vector((0,-1,0))
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
for a in list(bpy.data.actions):
 if not a.use_fake_user:continue
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];end=int(a.frame_range[1]);poses=[]
 for f in range(end+1):
  sc.frame_set(f);target=-3 if a.name in ['Standing','Walking'] else -6;w=1
  if a.name=='Hit':w=1-smooth(f/4)*smooth((end-f)/4)
  if a.name=='Death':w=1-smooth(f/8)
  F=(armik.W(r,'B_Head').to_3x3()@rest).normalized();pitch=math.atan2(F.z,math.hypot(F.x,F.y));delta=(math.radians(target)-pitch)*w;delta=max(-.6,min(.6,delta));axis=F.cross(Vector((0,0,1))).normalized()
  for n in ['B_Neck','B_Head']:
   M=armik.W(r,n).copy();Q=Quaternion(axis,delta*.5);armik.set_world(r,n,armik.rot_world(M,Q.to_matrix()@M.to_3x3().normalized()))
  poses.append({n:r.pose.bones[n].rotation_quaternion.copy() for n in ['B_Neck','B_Head']})
 prev={}
 for f,pose in enumerate(poses):
  for n,q in pose.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/all_motion_clear.blend'))
