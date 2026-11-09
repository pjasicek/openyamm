import bpy,sys,math,json,runpy,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;names=[b.name for b in rig.pose.bones]
code=(P/'scripts/motion.py').read_text();exec(code[code.index('def action'):code.index('baseline=')])
a=bpy.data.actions['Death'];frames=[sample(a,f)for f in range(int(a.frame_range[1])+1)];nf=len(frames)-1
for f,p in enumerate(frames):
 put(p);w=smooth((f/nf-.45)/.55)
 for s,sign in [('L',1),('R',-1)]:
  th,ca,ft=[f'B_{s}_'+n for n in ['Thigh','Calf','Foot']];H=rig.pose.bones[th].head.copy();K=rig.pose.bones[ca].head.copy();A=rig.pose.bones[ft].head.copy();L=(K-H).length+(A-K).length;target=H+Vector((sign*.015,L*.990,.012));target=A.lerp(target,w);R=wm(ft).to_3x3()
  aa=(K-H).length;bb=(A-K).length;u=(target-H).normalized();d=min((target-H).length,(aa+bb)*.9999);v=Vector((0,0,1));v=(v-u*v.dot(u)).normalized();c=(aa*aa+d*d-bb*bb)/(2*aa*d);E=H+aa*(u*c+v*math.sqrt(max(0,1-c*c)))
  aim(th,ca,E-H);aim(ca,ft,target-rig.pose.bones[ca].head);rotation(ft,R)
 frames[f]=get()
action(a)
for f,p in enumerate(frames):
 for s in 'LR':
  for part in ['Thigh','Calf','Foot','Toe0']:
   n=f'B_{s}_{part}';pb=rig.pose.bones[n];pb.rotation_quaternion=p[n][0];pb.keyframe_insert('rotation_quaternion',frame=f)
a=bpy.data.actions['Dead'];action(a)
for f in range(31):
 for n,(q,l,s)in frames[-1].items():
  if n.startswith('Skirt_'):continue
  pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=s;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
runpy.run_path(str(P/'scripts/cloth_fit.py'),run_name='__main__')
