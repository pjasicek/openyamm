"""Fit the long tail around the body while preserving the selected source casting and falling gestures."""
import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/actions.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
G=json.loads((P/'work/grip_pose.json').read_text());ax=Vector(G['handle_axis_hand_local']);ARM=['B_R_Clavicle','B_R_UpperArm','B_R_Forearm','B_R_Hand']
def ease(t):t=np.clip(t,0,1);return float(t*t*(3-2*t))
for name in ['Attack','Death']:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];frames=[];end=int(act.frame_range[1])
 for f in range(end+1):
  sc.frame_set(f);snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};H=armik.W(rig,'B_R_Hand');target=H.translation.copy();original=(H.to_3x3()@ax).normalized()
  if name=='Attack':
   u=min(ease(f/10),ease((end-f)/10));target.x+=(min(target.x,-.38)-target.x)*u
   target.y+=(min(target.y,-.30)-target.y)*u
   target.z+=(min(target.z,1.22)-target.z)*u
   clear=Vector((-.08,-.38,.92)).normalized();direction=original.lerp(clear,u).normalized()
  else:
   u=ease((f-15)/6);v=ease((f-22)/8);goal=Vector((-.30,.65,.35)).lerp(Vector((-.32,.57,-.02)),v);target=target.lerp(goal,u);direction=original.lerp(Vector((0,-1,0)),ease((f-12)/7)).normalized()
  frames.append({'snap':snap,'wrist':target,'dir':direction})
 rig.animation_data.action=None
 ch=armik.arm_dp(rig,'R',frames,ax,phis=range(-160,161,10),k_twist=.6,k_dphi=1.2,k_dpsi=1.1)
 # Smooth the selected plane and roll; use unwrapped roll to preserve rotation direction.
 def smooth(v):
  k=np.exp(-.5*(np.arange(-3,4)/1.25)**2);k/=k.sum();return np.convolve(np.pad(v,3,mode='edge'),k,'valid')
 ph=smooth([x['phi'] for x in ch]);ps=smooth(np.degrees(np.unwrap(np.radians([x['psi'] for x in ch]))));poses=[]
 for i,fr in enumerate(frames):
  armik.apply_arm(rig,'R',fr['snap'],fr['wrist'],ax,fr['dir'],ph[i],ps[i]);poses.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in ARM})
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for f,pose in enumerate(poses):
  sc.frame_set(f)
  for n,q in pose.items():
   if f and q.dot(poses[f-1][n])<0:q=-q
   b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
 print('STAFF ARM',name,'wrist swing',max(x['swing'] for x in ch),'twist',min(x['twist'] for x in ch),max(x['twist'] for x in ch))
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/actions.blend'))
