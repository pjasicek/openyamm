import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;G=json.loads((P/'work/grip_pose.json').read_text());B=rig.data.bones['Club'];axis=(B.tail_local-B.head_local).normalized();M=axis.to_track_quat('Z','Y').to_matrix().to_4x4();M.translation=B.head_local;bone_from_design=B.matrix_local.inverted()@M;parkM=M.copy();parkM.translation.x-=.04
pelrest=rig.data.bones['B_Pelvis'].matrix_local.copy();handCenter=Vector(G['handle_centre_hand_local']);handAxis=Vector(G['handle_axis_hand_local'])
def smooth(x):x=min(1,max(0,x));return x*x*(3-2*x)
motion={}
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];keys=[];prev=None
 for f in np.arange(0,float(a.frame_range[1])+.001,.5):
  scene.frame_set(int(f),subframe=float(f%1))
  localPark=parkM.copy()
  if a.name in ['Walking','Running','Death']:localPark.translation.y+=.16
  if a.name=='Death':localPark.translation.x-=.12
  Mp=rig.pose.bones['B_Pelvis'].matrix@pelrest.inverted()@localPark
  if a.name=='Attack':
   H=rig.pose.bones['B_R_Hand'].matrix;C=H@handCenter;A=(H.to_3x3()@handAxis).normalized();Qh=A.to_track_quat('Z','Y')
   w=smooth(f/6)*smooth((float(a.frame_range[1])-f)/7.5)
   Md=Mp.to_quaternion().slerp(Qh,w).to_matrix().to_4x4();Md.translation=Mp.translation.lerp(C,w)
   outward=(rig.pose.bones['B_Pelvis'].matrix.to_3x3()@pelrest.to_3x3().inverted()@Vector((-1,0,0))).normalized();Md.translation+=outward*(.12*math.sin(math.pi*w))
  elif a.name in ['Death','Dead']:
   pelvis=rig.pose.bones['B_Pelvis'].head;outward=rig.pose.bones['B_Pelvis'].matrix.to_3x3()@pelrest.to_3x3().inverted()@Vector((-1,0,0));outward.z=0;outward.normalize();outward=Vector((-1,0,0));C=pelvis+outward*.65;C.z=.060
   feet=(rig.pose.bones['B_L_Foot'].head+rig.pose.bones['B_R_Foot'].head)*.5;axis=feet-pelvis;axis.z=0;axis.normalize();Qh=axis.to_track_quat('Z','Y');w=1 if a.name=='Dead'else smooth((float(f)/float(a.frame_range[1])-.05)/.45)
   Md=Mp.to_quaternion().slerp(Qh,w).to_matrix().to_4x4();Md.translation=Mp.translation.lerp(C,w)
  else:Md=Mp
  B=Md@bone_from_design.inverted()
  if a.name in ['Death','Dead']:
   transform=B@rig.data.bones['Club'].matrix_local.inverted();low=min((transform@v.co).z for v in bpy.data.objects['ClubMesh'].data.vertices);B.translation.z+=max(0,.005-low)
  pb=rig.pose.bones['Club'];pb.rotation_mode='QUATERNION';pb.matrix=B
  q=pb.rotation_quaternion.copy()
  if prev is not None and q.dot(prev)<0:q=-q
  prev=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f));pb.keyframe_insert('location',frame=float(f))
  tip=Md@Vector((0,0,.452));keys.append([float(f/30),*tip,*Md.translation])
 motion[a.name]=keys

bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/prop_fixed.blend'))
