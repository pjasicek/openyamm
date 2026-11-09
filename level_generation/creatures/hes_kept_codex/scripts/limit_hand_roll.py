"""Smoothly cap unarmed punch wrist roll at 88 degrees, preserving its swing and trajectory."""
import bpy,sys,os,math
from pathlib import Path
import numpy as np
from mathutils import Quaternion,Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import armik
src,out=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));r=bpy.data.objects['Rig'];a=bpy.data.actions['Kept_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene
for sd in 'LR':
 pb=r.pose.bones[f'B_{sd}_Hand'];keys=[];delta=0
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));q=pb.rotation_quaternion.copy();s,t=armik.split_swing_twist(q,Vector((0,1,0)));d=math.degrees(t)
  capped=math.copysign(75+13*math.tanh((abs(d)-75)/13),d) if abs(d)>75 else d
  q=s@Quaternion((0,1,0),math.radians(capped));delta=max(delta,abs(d-capped));keys.append((float(f),q))
 prev=None
 for f,q in keys:
  if prev is not None and q.dot(prev)<0:q.negate()
  prev=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
 print('PUNCH_ROLL',sd,'max correction deg',delta,flush=True)
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
