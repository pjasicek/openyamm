import bpy,sys,runpy,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1]
sys.argv=['retarget_mixamo.py','--',str(P/'work/rig_motion.blend'),str(P/'work/death_mixamo.blend'),str(P.parents[2]/'anim_library/mixamo/Falling Forward Death.fbx')+':DeathNew:turn'];runpy.run_path(str(P/'scripts/retarget_mixamo.py'),run_name='__main__')
sys.argv=['retarget.py','--',str(P/'work/rig_motion.blend'),str(P/'work/attack_planted.blend'),str(P.parents[2]/'anim_library/humanoid_set/1Hand.glb')+':DaggerAttackR3:AttackNew:plant'];runpy.run_path(str(P/'scripts/retarget.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;names=[b.name for b in rig.pose.bones]
code=(P/'scripts/motion.py').read_text();exec(code[code.index('def action'):code.index('baseline=')])
native=sample(bpy.data.actions['Standing'],0);core=set(json.loads(sc['rig_offsets']));G=json.loads((P/'work/grip_pose.json').read_text());out={}
for filename,an,name in [('death_mixamo.blend','DeathNew','Death'),('attack_planted.blend','AttackNew','Attack')]:
 with bpy.data.libraries.load(str(P/'work'/filename),link=False)as(src,dst):dst.actions=[an]
 raw=dst.actions[0];nf=int(raw.frame_range[1]);frames=[]
 for f in range(nf+1):
  p=sample(raw,f)
  for n in names:
   if n not in core:p[n]=native[n]
  w=smooth(f/7)*(smooth((nf-f)/7)if name=='Attack'else 1);put(blend(native,p,w))
  for pb in rig.pose.bones:
   if 'Finger'in pb.name:pb.rotation_quaternion=Quaternion(G['finger_local'][pb.name])if name=='Attack'and pb.name in G['finger_local']else Quaternion()
  rig.pose.bones['Knife'].scale=(1,)*3 if name=='Attack'else(.001,)*3
  if name=='Attack':
   for n in ['B_Spine','B_Spine1','B_Spine2']:rig.pose.bones[n].rotation_quaternion=native[n][0].slerp(rig.pose.bones[n].rotation_quaternion,.6)
   bpy.context.view_layer.update()
   for sd,sign in [('L',1),('R',-1)]:
    ft=f'B_{sd}_Foot';T=rig.data.bones[ft].head_local.copy();T.x=sign*.102;T.z+=.002;T.y+=(.022 if sd=='R'else-.015)*math.sin(math.pi*f/nf)**2
    if sd=='R'and .2<f/nf<.42:T.z+=.015*math.sin(math.pi*(f/nf-.2)/.22)**2
    leg(sd,T,rig.data.bones[ft].matrix_local.to_3x3())
   # An empty balancing hand stays beside the skirt, while the knife arm keeps the source action.
   sd='L';U,F,H=[f'B_{sd}_'+n for n in ['UpperArm','Forearm','Hand']];S=rig.pose.bones[U].head.copy();E=rig.pose.bones[F].head.copy();W=rig.pose.bones[H].head.copy();T=Vector((.265,-.04-.035*math.sin(math.pi*f/nf)**2,.79));aa=(E-S).length;bb=(W-E).length;u=(T-S).normalized();d=min((T-S).length,(aa+bb)*.999);v=Vector((.2,.9,0));v=(v-u*v.dot(u)).normalized();c=(aa*aa+d*d-bb*bb)/(2*aa*d);K=S+aa*(u*c+v*math.sqrt(max(0,1-c*c)));aim(U,F,K-S);aim(F,H,T-rig.pose.bones[F].head)
   rel=rig.data.bones[F].matrix_local.to_3x3().inverted()@rig.data.bones[H].matrix_local.to_3x3();rotation(H,wm(F).to_3x3()@rel)
  else:
   pb=rig.pose.bones['B_Pelvis'];M=wm(pb.name)
   if f==0:origin=M.translation.copy()
   M.translation.x=origin.x+(M.translation.x-origin.x)*.3;M.translation.y=origin.y+(M.translation.y-origin.y)*.3;pb.matrix=M;bpy.context.view_layer.update()
  for sd in 'LR':anatomical(sd)
  frames.append(get())
 out[name]=frames;action(None);bpy.data.actions.remove(raw)
out['Dead']=[out['Death'][-1]]*31
for name,frames in out.items():
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;action(a);prev={}
 for f,p in enumerate(frames):
  for n,(q,l,s)in p.items():
   pb=rig.pose.bones[n]
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb.rotation_quaternion=q;pb.location=l;pb.scale=s;pb.keyframe_insert('rotation_quaternion',frame=f)
   pb.keyframe_insert('location',frame=f)
   if n=='Knife':pb.keyframe_insert('scale',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(frames)-1;action(None)
# Floor placement uses the body, before the garment simulation; cloth must resolve its own contact.
b=bpy.data.objects['Body'];pv=np.array([x.value for x in b.data.attributes['piece'].data]);ids=np.flatnonzero(~np.isin(pv,[1,3]));root=rig.pose.bones['B_Pelvis'];inv=rig.data.bones[root.name].matrix_local.to_3x3().inverted()
for name in ['Death','Dead']:
 a=bpy.data.actions[name];action(a);nf=int(a.frame_range[1]);loc=[];corr=[0.]*(nf+1)
 for f in range(nf+1):sc.frame_set(f);loc.append(root.location.copy())
 for t in np.linspace(0,nf,math.ceil(nf*48/30)+1):
  sc.frame_set(int(t),subframe=float(t%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();dz=max(0,.001-min(me.vertices[int(i)].co.z for i in ids));ev.to_mesh_clear()
  for j in {int(t),min(nf,math.ceil(t))}:corr[j]=max(corr[j],dz)
 for f,l in enumerate(loc):root.location=l+inv@Vector((0,0,corr[f]));root.keyframe_insert('location',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
