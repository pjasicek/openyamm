"""Spread the late pelvis surge into the approach; preserve the accepted synchronized recovery."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
B=P/'work/review_round6_before';end=55
bpy.ops.wm.open_mainfile(filepath=str(B/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig'];poses=[]
def ease(t):
 t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))
for f in range(end+1):
 C.activate('Attack',(f if f<43 else f+2)/48)
 row={b.name:b.matrix_basis.copy()for b in r.pose.bones}
 if 32<f<43:
  targets={sd:r.pose.bones[f'B_{sd}_Foot'].matrix.copy()for sd in 'LR'}
  r.animation_data.action=None
  shift=.30*((.97*ease((f-32)/8)+.03*ease((f-32)/11))-ease((f-42)/3))
  m=r.pose.bones['B_Pelvis'].matrix.copy();m.translation.y-=shift;r.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
  # Keep the original foot placements while spreading the pelvis drive over eight frames.
  for sd in 'LR':
   ns=[f'B_{sd}_{n}'for n in ['Thigh','Calf','Foot']];H,K,A=[r.pose.bones[n].head.copy()for n in ns];aa=(K-H).length;bb=(A-K).length;target=targets[sd].translation;u=(target-H).normalized();dist=min((target-H).length,(aa+bb)*.997);v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();xx=(aa*aa+dist*dist-bb*bb)/(2*dist);knee=H+u*xx+v*math.sqrt(max(0,aa*aa-xx*xx))
   for n,c,T in [(ns[0],ns[1],knee),(ns[1],ns[2],H+u*dist)]:
    pb=r.pose.bones[n];q=(r.pose.bones[c].head-pb.head).rotation_difference(T-pb.head);m=(q@pb.matrix.to_quaternion()).to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update()
   pb=r.pose.bones[ns[2]];m=targets[sd].copy();m.translation=pb.head;pb.matrix=m;bpy.context.view_layer.update()
  row={b.name:b.matrix_basis.copy()for b in r.pose.bones}
 poses.append(row)
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(B/f'work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];bpy.data.actions.remove(bpy.data.actions['Attack']);a=bpy.data.actions.new('Attack');a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=end;r.animation_data.action=a;previous={}
 for f,row in enumerate(poses):
  for n,m in row.items():
   pb=r.pose.bones[n];pb.matrix_basis=m;q=pb.rotation_quaternion
   if n in previous and previous[n].dot(q)<0:q.negate()
   previous[n]=q.copy();pb.rotation_quaternion=q
   for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=f,group=n)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for key in curve.keyframe_points:key.interpolation='LINEAR'
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
 if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
s=(P/'scripts/quick_export.py').read_text().replace('range(4)','range(1)').replace('export/mm6_natm_raw_lod{level}.glb','work/round6_animation.glb');exec(compile(s,str(P/'scripts/quick_export.py'),'exec'))
