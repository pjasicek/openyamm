import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/cloth_fit.blend'));r=bpy.data.objects['Rig'];s=bpy.context.scene;body=bpy.data.objects['Body'];G=json.loads((P/'work/round2/grip_pose.json').read_text())
def frame(f):s.frame_set(int(f),subframe=f%1)
def smooth(t):t=float(np.clip(t,0,1));return t*t*(3-2*t)
# Replace interleaved old 120 Hz root-translation keys with the complete smoothed 30 Hz correction field.
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     if 'Cloak_'in fc.data_path and '_0"].location'in fc.data_path:
      keep=[(k.co.x,k.co.y)for k in fc.keyframe_points if abs(k.co.x-round(k.co.x))<1e-4 or abs(k.co.x-a.frame_range[1])<1e-4];fc.keyframe_points.clear();fc.keyframe_points.add(len(keep))
      for k,co in zip(fc.keyframe_points,keep):k.co=co;k.interpolation='LINEAR'
      fc.update()
B=r.data.bones['Club'];axis=(B.tail_local-B.head_local).normalized();design=axis.to_track_quat('Z','Y').to_matrix().to_4x4();design.translation=B.head_local;bone_from_design=B.matrix_local.inverted()@design
park=Vector((-.248,.105,.91));parkQ=Vector((-.16,.10,-1)).normalized().to_track_quat('Z','Y');parkM=parkQ.to_matrix().to_4x4();parkM.translation=park;pr=r.data.bones['B_Pelvis'].matrix_local;hc=Vector(G['handle_centre_hand_local']);ha=Vector(G['handle_axis_hand_local'])
a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];frames=np.arange(0,float(a.frame_range[1])+.001,.25);old=[]
for f in frames:
 frame(f);old.append({n:r.pose.bones[n].rotation_quaternion.copy()for n in G['finger_local']})
frame(0);H=r.pose.bones['B_R_Hand'].matrix;heldLocal=H.to_quaternion().inverted()@(H.to_3x3()@ha).to_track_quat('Z','Y');prev={}
for f,qs in zip(frames,old):
 frame(f);w=smooth(f/6)*smooth((float(frames[-1])-f)/7.5)
 for n,q0 in qs.items():
  b=r.pose.bones[n];q=q0.slerp(Quaternion(G['finger_local'][n]),w)
  if n in prev and q.dot(prev[n])<0:q=-q
  prev[n]=q;b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=float(f))
 bpy.context.view_layer.update();M=r.pose.bones['B_Pelvis'].matrix@pr.inverted()@parkM;H=r.pose.bones['B_R_Hand'].matrix;Q=M.to_quaternion().slerp(H.to_quaternion()@heldLocal,w);C=M.translation.lerp(H@hc,w)
 # Pull outward while drawing/returning, with both endpoints fixed to their real socket.
 C+=(r.pose.bones['B_Pelvis'].matrix@pr.inverted()).to_3x3()@Vector((-.10*math.sin(math.pi*w),0,0));M=Q.to_matrix().to_4x4();M.translation=C;b=r.pose.bones['Club'];b.matrix=M@bone_from_design.inverted();q=b.rotation_quaternion.copy()
 if 'Club'in prev and q.dot(prev['Club'])<0:q=-q
 prev['Club']=q;b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=float(f));b.keyframe_insert('location',frame=float(f))
# Synchronize terminal hold after all new motion.
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];frame(float(a.frame_range[1]));terminal={b.name:b.matrix_basis.copy()for b in r.pose.bones};r.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;r.animation_data.action=a
for f in [0,30]:
 for b in r.pose.bones:
  b.matrix_basis=terminal[b.name]
  for field in ['location','rotation_quaternion','scale']:b.keyframe_insert(field,frame=f)
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/master.blend'))
common.workbench_clay(s,True);s.display.shading.show_specular_highlight=False
for role,t in [('Standing',0),('Running',.2),('Attack',.8),('Death',1),('Death',2.36),('Dead',0)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];frame(t*30);lo,hi=common.world_bounds([body,bpy.data.objects['ClubMesh']]);mid=(lo+hi)/2
 common.render_views(str(P/'review/round2'/f'fit_{role}_{t}'),mid.z,max(2.05,(hi-lo).length),views=('front','left','three_quarter'),target=(mid.x,mid.y),resolution=(600,800))
