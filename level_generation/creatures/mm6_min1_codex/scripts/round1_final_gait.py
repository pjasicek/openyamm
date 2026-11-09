"""Preserve all validated action samples, enforce travel-aligned ankles and freeze one action set."""
import bpy,sys,runpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_fit as F
bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_master.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;F.r=r;F.body=b;F.sc=sc
r.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(P/'work/round1_timefit.blend'),link=False) as (src,dst):dst.actions=F.roles
for a in dst.actions:a.use_fake_user=True
xyz=np.array([v.co[:] for v in b.data.vertices]);F.sole={s:np.where((xyz[:,2]<.025)&(xyz[:,0]*sign>0))[0] for s,sign in [('R',-1),('L',1)]}
for role in ['Walking','Running']:
 a=bpy.data.actions[role];rows=[]
 for f in range(round(a.frame_range[1])+1):
  F.apply(F.sample(a,f))
  for s in 'RL':
   foot=F.M(f'B_{s}_Foot');v=foot.to_3x3()@F.restb[f'B_{s}_Foot'].to_3x3().inverted()@Vector((0,-1,0));yaw=math.atan2(v.x,-v.y);old=float(F.coords()[F.sole[s],2].min());rot=Matrix.Rotation(-yaw,3,'Z')@foot.to_3x3();F.leg(s,foot.translation,rot);dz=old-float(F.coords()[F.sole[s],2].min());foot=F.M(f'B_{s}_Foot');F.leg(s,foot.translation+Vector((0,0,dz)),rot)
  rows.append(F.snapshot())
 bpy.data.actions.remove(a);a=bpy.data.actions.new(role);a.use_fake_user=True;prev={}
 for f,row in enumerate(rows):
  F.apply(row);r.animation_data.action=a
  for n in F.names:
   pb=r.pose.bones[n];q=pb.matrix_basis.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q.negate()
   prev[n]=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  r.animation_data.action=None
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/production_master.blend'))
sys.argv=['gate','--','work/production_master.blend'];runpy.run_path(str(P/'scripts/rig_gates_48.py'))
runpy.run_path(str(P/'scripts/round1_precision.py'),init_globals={'INPUT':'work/production_master.blend'})
runpy.run_path(str(P/'scripts/round1_acceleration.py'),init_globals={'INPUT':'work/production_master.blend'})
assert all(all(v['pass'].values()) for v in json.loads((P/'review/rig_gates.json').read_text()).values())
assert all(v['pass'] for v in json.loads((P/'review/round1/precision_gate.json').read_text()).values())
assert json.loads((P/'review/round1/acceleration_gate.json').read_text())['pass']
