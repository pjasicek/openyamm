import bpy,sys,math,json,runpy,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;names=[b.name for b in rig.pose.bones]
code=(P/'scripts/motion.py').read_text();exec(code[code.index('def action'):code.index('baseline=')]);rest={n:(Quaternion(v[0]),Vector(v[1]),Vector(v[2]))for n,v in json.loads((P/'work/native_rest.json').read_text()).items()}
for name in ['Walking','Running']:
 a=bpy.data.actions[name];frames=[sample(a,f)for f in range(int(a.frame_range[1])+1)];nf=len(frames)-1
 for f,p in enumerate(frames):
  put(p);t=f/nf;n='B_Pelvis';rig.pose.bones[n].location=rest[n][1]+rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((0,0,-(.09 if name=='Running'else .045)*math.sin((t-(.26 if name=='Running'else .30))*math.tau)**2));bpy.context.view_layer.update()
  for sd,sign in [('L',1),('R',-1)]:
   ft=f'B_{sd}_Foot';T=rig.data.bones[ft].head_local.copy();T.x=sign*.102;T.z+=.002;R=rig.data.bones[ft].matrix_local.to_3x3();phase=(t+(0 if sd=='L'else .5))%1;duty=.52 if name=='Running'else .60;stride=.3627 if name=='Running'else .27
   if phase<duty:T.y+=-stride+2*stride*phase/duty
   else:u=(phase-duty)/(1-duty);T.y+=stride-2*stride*smooth(u);T.z+=.085*math.sin(math.pi*u)**1.3
   leg(sd,T,R)
  frames[f]=get()
 action(a)
 for f,p in enumerate(frames):
  for n,(q,l,s)in p.items():
   if n=='B_Pelvis'or any(x in n for x in ['Thigh','Calf','Foot','Toe']):
    pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f)
    if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))

runpy.run_path(str(P/'scripts/final_skirt.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/final_secondary.py'),run_name='__main__')
