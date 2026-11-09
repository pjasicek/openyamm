"""Finish only the three armed-library candidates; accepted actions remain untouched."""
import bpy,sys,os,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import armik
path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];sc=bpy.context.scene;body=bpy.data.objects['Kept'];D=np.load(P/'texturing/kept_m_uv.npz');pc=np.zeros(len(body.data.vertices),int)
for face,part in zip(D['faces'],D['piece']):pc[face]=part
if 'piece' not in body.data.attributes:body.data.attributes.new('piece','INT','POINT')
body.data.attributes['piece'].data.foreach_set('value',pc)
def twist_about(q,axis):return (2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi
for a in bpy.data.actions:
 if not a.name.startswith('Kept_Club'):continue
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 # Keep the elbow within the covered sleeve range while preserving the source arm plane.
 keys=[]
 for f in np.arange(0,a.frame_range[1]+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1));S=armik.W(r,'B_R_UpperArm').translation;E=armik.W(r,'B_R_Forearm').translation;H=armik.W(r,'B_R_Hand');u=(E-S).length;v=(H.translation-E).length;reach=math.sqrt(u*u+v*v+2*u*v*math.cos(math.radians(55)))
  delta=H.translation-S
  if delta.length<reach:armik.solve(r,'R',S+delta.normalized()*reach,hand_rot=H.to_3x3().normalized())
  keys.append((float(f),{n:r.pose.bones[n].rotation_quaternion.copy() for n in ('B_R_UpperArm','B_R_Forearm','B_R_Hand')}))
 for f,qs in keys:
  for n,q in qs.items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
 for sd in 'LR':
  p=r.pose.bones[f'B_{sd}_Hand'];keys=[]
  for f in np.arange(0,a.frame_range[1]+.001,.5):
   sc.frame_set(int(f),subframe=float(f%1));s,t=armik.split_swing_twist(p.rotation_quaternion,Vector((0,1,0)))
   if s.w<0:s=-s
   angle=s.angle
   if angle>math.radians(58):s=Quaternion().slerp(s,math.radians(58)/angle)
   t=math.copysign(math.radians(75)+math.radians(13)*math.tanh((abs(t)-math.radians(75))/math.radians(13)),t) if abs(t)>math.radians(75) else t
   keys.append((float(f),s@Quaternion((0,1,0),t)))
  prev=None
  for f,q in keys:
   if prev is not None and q.dot(prev)<0:q=-q
   prev=q.copy();p.rotation_quaternion=q;p.keyframe_insert('rotation_quaternion',frame=f)
 for f in np.arange(0,a.frame_range[1]+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1))
  for sd in 'LR':
   fb,hb=r.data.bones[f'B_{sd}_Forearm'],r.data.bones[f'B_{sd}_Hand'];axis=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(r.pose.bones[fb.name].matrix.inverted()@r.pose.bones[hb.name].matrix).to_quaternion();rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();p=r.pose.bones[f'B_{sd}_ForearmTwist'];p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion(axis,.6*twist_about(rel@rest.inverted(),axis));p.keyframe_insert('rotation_quaternion',frame=float(f))
   ub=r.data.bones[f'B_{sd}_UpperArm'];axis=(ub.matrix_local.inverted()@fb.head_local).normalized();q=r.pose.bones[ub.name].matrix_basis.to_quaternion();p=r.pose.bones[f'B_{sd}_UpperArmTwist'];p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion(axis,-.5*twist_about(q,axis));p.keyframe_insert('rotation_quaternion',frame=float(f))
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(path));print('CANDIDATES_FINISHED',flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
