"""Bake fixed two-hand frames at 120 Hz, including the viewer's intermediate samples."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_fit as F
bpy.ops.wm.open_mainfile(filepath=str(P/globals().get('INPUT','work/round1_relaxed.blend')));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;F.r=r;F.body=b;F.sc=sc;meta=json.loads((P/'work/round1_grip_frames.json').read_text());HF={s:Matrix(meta['frames'][s]) for s in 'RL'};zs=meta['grip_z'];AR=Matrix(meta['right_hand_to_axe']);axerest=r.data.bones['Axe'].matrix_local;result={};metrics={}
for a in list(bpy.data.actions):
 rows=[];stats=[]
 for i in range(round(a.frame_range[1]*240/sc.render.fps)+1):
  t=i/240;row=F.sample(a,t*sc.render.fps);F.apply(row)
  if a.name!='Dead' and not(a.name=='Death' and t>1/6):
   A=F.M('Axe')@axerest.inverted();pref={s:F.M(f'B_{s}_Forearm').translation for s in 'RL'}
   for s in 'RL':
    HR=A.to_3x3()@HF[s];target=A@Vector((0,0,zs[s]))-HR@Vector(F.G[s]['handle_centre_hand_local']);stats.append([t,s]+F.solvearm(s,target,HR,pref[s]))
   F.setmat('Axe',F.M('B_R_Hand')@AR@axerest)
  for s in 'RL':
   un,fn,hn,la,lb,ru,rf,rb,axis=F.armdata[s];U,EL,H=[F.M(n).translation for n in [un,fn,hn]];up=(EL-U).normalized();fo=(H-EL).normalized();bend=(fo-up*fo.dot(up)).normalized();UR=F.basis(up,bend)@rb.transposed()@F.restb[un].to_3x3();fm=F.M(fn);hm=F.M(hn);F.setmat(un,F.transform(UR,U));F.setmat(fn,fm);F.setmat(hn,hm);ua=(F.restb[un].inverted()@F.restb[fn].translation).normalized();tw=F.twist(r.pose.bones[un].rotation_quaternion,ua);r.pose.bones[f'B_{s}_UpperArmTwist'].rotation_quaternion=Quaternion(ua,-.5*tw)
  F.update()
  if a.name not in ['Death','Dead']:
   for s in 'RL':
    foot=F.M(f'B_{s}_Foot');v=foot.to_3x3()@F.restb[f'B_{s}_Foot'].to_3x3().inverted()@Vector((0,-1,0));yaw=math.atan2(v.x,-v.y);old=float(F.coords()[F.sole[s],2].min());rot=Matrix.Rotation(-yaw,3,'Z')@foot.to_3x3();F.leg(s,foot.translation,rot);dz=old-float(F.coords()[F.sole[s],2].min());foot=F.M(f'B_{s}_Foot');F.leg(s,foot.translation+Vector((0,0,dz)),rot)
  if a.name in ['Standing','Fidget']:

   for s in 'RL':F.flatten(s)
  rows.append(F.snapshot())
 result[a.name]=rows;metrics[a.name]=stats;print('DENSE',a.name,len(rows),flush=True)
sc.render.fps=240;sc.render.fps_base=1
for nm,rows in result.items():
 bpy.data.actions.remove(bpy.data.actions[nm]);a=bpy.data.actions.new(nm);a.use_fake_user=True;prev={}
 for i,row in enumerate(rows):
  F.apply(row);r.animation_data.action=a
  for n in F.names:
   pb=r.pose.bones[n];q=pb.matrix_basis.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q.negate()
   prev[n]=q.copy();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=i);pb.keyframe_insert('location',frame=i)
  r.animation_data.action=None
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
 for la in a.layers:
  for st in la.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
(P/'review/round1/dense_fit.json').write_text(json.dumps(metrics,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_dense.blend'))
