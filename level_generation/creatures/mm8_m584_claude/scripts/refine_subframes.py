"""Bake exact two-hand grip and floor constraints at the exported 60 Hz samples."""
from pathlib import Path
import bpy,sys,json,math
import numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/authored.blend'))
r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'LR'}
GC={s:Vector(G[s]['handle_centre_hand_local']) for s in 'LR'};GA={s:Vector(G[s]['handle_axis_hand_local']) for s in 'LR'}
attack=bpy.data.actions['Attack']
for layer in attack.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for key in fc.keyframe_points:
     key.co.x=float(np.interp(key.co.x,[0,15,19.2,26.4,39],[0,26,29,33,35]))
     key.handle_left.x=key.co.x;key.handle_right.x=key.co.x
    fc.update()
attack.frame_end=35
report={}
for a in list(bpy.data.actions):
 if not a.use_fake_user:continue
 poses=[];end=a.frame_range[1];maximum=0
 for frame in np.arange(0,end+.01,.5):
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(frame),subframe=float(frame-int(frame)))
  pose={b.name:b.matrix_basis.copy() for b in r.pose.bones};r.animation_data.action=None
  for n,m in pose.items():r.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update()
  held=a.name not in ('Death','Dead') or (a.name=='Death' and frame<=18)
  if held:
   H=armik.W(r,'B_R_Hand');C=H@GC['R'];A=(H.to_3x3()@GA['R']).normalized()
   W=armik.W(r,'Polearm');N=W.to_3x3()@Vector((0,0,1));N=(N-A*N.dot(A)).normalized()
   W=Matrix((A.cross(N),A,N)).transposed().to_4x4();slide=0
   if a.name=='Death':
    u=max(0,min(1,(frame/30-.333333)/.266667));slide=.48*u*u*(3-2*u)
   W.translation=C+A*slide;armik.set_world(r,'Polearm',W)
   H=armik.W(r,'B_L_Hand');R=(H.to_3x3()@GA['L']).rotation_difference(A).to_matrix()@H.to_3x3()
   target=C-A*.24-R@GC['L'];maximum=max(maximum,(target-H.translation).length)
   armik.solve(r,'L',target,hand_rot=R)
  if a.name in ('Death','Dead'):
   W=armik.W(r,'Polearm').copy();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
   low=min(v.co.z for v in me.vertices if body.data.attributes['piece'].data[v.index].value<1000);ev.to_mesh_clear()
   if low<0:
    m=armik.W(r,'B_Pelvis');m.translation.z-=low;armik.set_world(r,'B_Pelvis',m)
    if not held:armik.set_world(r,'Polearm',W)
  poses.append((float(frame),{b.name:b.matrix_basis.copy() for b in r.pose.bones}))
 old=a.name;bpy.data.actions.remove(a);a=bpy.data.actions.new(old);a.use_fake_user=True;r.animation_data.action=a;prev={}
 for f,p in poses:
  for n,m in p.items():
   l,q,_=m.decompose();b=r.pose.bones[n];b.rotation_mode='QUATERNION'
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();b.rotation_quaternion=q;b.location=l;b.scale=(1,1,1)
   b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=end
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[old]={'duration':end/30,'grip_adjustment_max_m':maximum,'sample_hz':60}
 print('REFINE',old,report[old],flush=True)
r.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/animation_constrained.blend'))
report['timing']={'native_impact':.875,'clip_impact':26/30,'basis':'No Raven Man override in sprite_attack_timing.yml; MM8 native action-end impact.'}
(P/'work/subframe_refinement.json').write_text(json.dumps(report,indent=2)+'\n')
