"""Native levitation and disappearance with owned source-frame dual-palm casting."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30
D=json.loads((P/'work/rig.json').read_text());B=D['bones'];R={n:rig.data.bones[n].matrix_local.copy() for n in B};REL={n:R[b['parent']].inverted()@R[n] if b['parent'] else R[n] for n,b in B.items()};SOURCE=json.loads((P/'work/source_motion.json').read_text())['UnarmedCastDualAttack2'];SRC=json.loads((P/'work/source_rest.json').read_text());C=np.array([v.co[:] for v in body.data.vertices]);E=np.array([e.vertices[:] for e in body.data.edges]);PA=np.array([v.value for v in body.data.attributes['part'].data]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1)
LOOPS={'Standing':3.,'Walking':1.2,'Running':.8,'Attack':1.5,'Cast':1.5,'Hit':.7333333333,'Fidget':2.4,'Death':1.8,'Dead':1.}
def ss(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
def env(t,a,b,c):return ss((t-a)/(b-a))*(1-ss((t-b)/(c-b)))
def matrix(q,p):m=q.to_matrix().to_4x4() if isinstance(q,Quaternion) else q.to_4x4();m.translation=Vector(p);return m
def rot(axis,angle):return Quaternion(axis,angle)
def setq(m,q):return matrix(q,m.translation)
def pose(role,t):
 if role=='Dead':role,t='Death',LOOPS['Death']
 cycle=2*math.pi*t/LOOPS[role];gait=role in ['Walking','Running'];run=role=='Running';action=role in ['Attack','Cast'];ct=t;wind=env(ct,0,.38,.76) if action else 0.;release=env(ct,.38,.78,1.45) if action else 0.;hit=env(t,0,.19,.73) if role=='Hit' else 0.;fidget=math.sin(cycle)*ss(t/.25)*(1-ss((t-2.15)/.25)) if role=='Fidget' else 0.;death=role=='Death';fall=ss((t-.18)/1.20) if death else 0
 M={'Root':R['Root'].copy()}
 pitch=(-.12*wind+.17*release-.19*hit)+(.14 if run else .065 if gait else .012*math.sin(cycle));yaw=.08*wind-.055*release+.09*fidget;bank=.045*math.sin(cycle) if gait else -.07*wind+.06*release
 q=rot((0,0,1),yaw)@rot((0,1,0),bank)@rot((1,0,0),pitch-2.6*fall)
 root=R['BodyRoot'].translation+Vector((.025*math.sin(cycle) if gait else -.035*wind+.045*release, .045*wind-.055*release,.025*math.sin(cycle)*(1-fall)))
 root.z-=.96*fall
 scale=max(.001,1-ss((t-.65)/.85)) if death else 1.
 M['BodyRoot']=matrix(q@R['BodyRoot'].to_quaternion(),root)@Matrix.Diagonal((scale,scale,scale,1))
 # Casting source clock retains its 30-Hz release/follow-through, preceded by a short ready blend.
 source_t=max(0,min(1.,ct-.20));k=source_t*30;i=min(int(k),len(SOURCE['keys'])-1);j=min(i+1,len(SOURCE['keys'])-1);blend=ss(max(ct,0)/.25)*(1-ss((ct-1.12)/.35)) if action else 0.
 def sq(n):return Quaternion(SOURCE['keys'][i][n]['q']).slerp(Quaternion(SOURCE['keys'][j][n]['q']),k-i)
 for n,b in B.items():
  if n in M or n.startswith('Gold'):continue
  par=b['parent'];m=M[par]@REL[n]
  if n.startswith('Vortex_'):
   idx=int(n[-2:]);amp=(.055 if run else .035 if gait else .015)*(1-fall);phase=cycle-idx*.48;local=Matrix.Rotation(amp*math.sin(phase),4,'X')@Matrix.Rotation(amp*.75*math.cos(phase),4,'Z');m=m@local
  elif n in ['B_Spine','B_Spine1','B_Spine2']:
   src_rest=Matrix(SRC[n]['rot']).to_quaternion();delta=sq(n)@src_rest.inverted() if action else Quaternion();dq=Quaternion().slerp(delta,.25*blend);m=setq(m,q@dq@R[n].to_quaternion());m=m@Matrix.Diagonal((scale,scale,scale,1))
  elif n in ['B_Neck','B_Head']:
   m=m@Matrix.Rotation((-.045*wind+.05*release) if n=='B_Head' else 0,4,'X')
   if n=='B_Head':m=m@Matrix.Rotation(.22*fidget,4,'Y')
  elif n.endswith('_Clavicle'):
   if action:m=setq(m,m.to_quaternion().slerp(q@sq(n),.25*blend))@Matrix.Diagonal((scale,scale,scale,1))
  elif n.endswith('_UpperArm') or n.endswith('_Forearm') or n.endswith('_Hand'):
   sd=n.split('_')[1];sign=1 if sd=='L' else -1
   # Native idle: arms lowered a little from the modelling A-pose, hands relaxed beside vortex.
   base=q@rot((0,1,0),sign*.09)@R[n].to_quaternion()
   if gait:base=q@rot((1,0,0),.04*math.sin(cycle+(0 if sd=='L' else math.pi)))@rot((0,1,0),sign*.09)@R[n].to_quaternion()
   if hit or fall:base=q@rot((0,1,0),-sign*(.22*hit+.35*fall))@R[n].to_quaternion()
   if fidget:base=q@rot((1,0,0),-.12*fidget*(1 if sd=='L' else .45))@R[n].to_quaternion()
   target=q@sq(n) if action else base;poseq=base.slerp(target,blend);m=setq(m,poseq)@Matrix.Diagonal((scale,scale,scale,1))
  elif '_Finger' in n:
   curl=.06+.12*wind-.05*release+.09*hit
   m=m@Matrix.Rotation(max(0,curl),4,'X')
  M[n]=m
 for pn,jewel in D['jewels'].items():
  n=jewel['bone'];follow=jewel['follow'];m=M[follow]@R[follow].inverted()@R[n]
  if death and t>.18:
   # Detach in world space while the body vanishes; three native golden remains settle independently.
   u=t-.18;idx=list(D['jewels']).index(pn);rest=R[n].translation;dest=Vector(([-.28,.26,-.10][idx],[.10,.04,-.20][idx],.05));a=ss(u/1.1);pos=rest.lerp(dest,a);pos.z=max(.05,rest.z+.65*u-2.9*u*u);spin=rot((1,.3,.2),min(u,1.1)*(2.4+idx*.6));m=matrix(spin@R[n].to_quaternion(),pos)
   vc=C[PA==int(pn)];deform=m@R[n].inverted();low=min((deform@Vector(v)).z for v in vc)
   if low<.008:m.translation.z+=.008-low
  M[n]=m
 for n,b in B.items():
  par=b['parent'];basis=REL[n].inverted()@(M[par].inverted()@M[n] if par else M[n]);rig.pose.bones[n].matrix_basis=basis
 bpy.context.view_layer.update()
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();low=min(v.co.z for v in mesh.vertices);ev.to_mesh_clear()
 if low<.008:
  name='BodyRoot' if death else 'Root';rig.pose.bones[name].location+=R[name].to_3x3().transposed()@Vector((0,0,.008-low));bpy.context.view_layer.update()
 return M
rig.animation_data_clear()
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
reports={};sheets=[]
for role,dur in LOOPS.items():
 count=round(dur*30);keys={n:[] for n in B};mins=[];ratio=[];first=None
 for f in range(count+1):
  rig.animation_data_clear();pose(role,f/30);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();first=c.copy() if first is None else first;mins.append(float(c[:,2].min()));stretch=np.linalg.norm(c[E[:,1]]-c[E[:,0]],axis=1)/np.maximum(EL,1e-9);mask=np.isin(PA[E[:,0]],[2,3])&np.isin(PA[E[:,1]],[2,3])&(EL>1e-4);ratio.append([float(np.percentile(stretch[mask],99)),float(stretch[mask].max())])
  for n in B:
   pb=rig.pose.bones[n];qq=pb.rotation_quaternion.copy()
   if keys[n] and qq.dot(keys[n][-1][1])<0:qq.negate()
   keys[n].append((pb.location.copy(),qq,pb.scale.copy()))
 action=bpy.data.actions.new(role);action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action
 for f in range(count+1):
  for n in B:
   pb=rig.pose.bones[n];pb.location,pb.rotation_quaternion,pb.scale=keys[n][f]
   for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=f+1,group=n)
 for layer in action.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 reports[role]={'duration':count/30,'min_z':min(mins),'skin_stretch_p99_max':np.max(ratio,axis=0).tolist(),'loop_delta':float(np.linalg.norm(c-first,axis=1).max())};print(role,reports[role])
 common.workbench_clay(sc)
 for f in [0,round(count*.25),round(count*.5),round(count*.75),count]:
  sc.frame_set(f+1);common.render_views(str(P/'review'/f'clay_{role}_{f:03}'),1.1,2.7,views=('front','three_quarter'),resolution=(400,540))
(P/'work/animation_audit.json').write_text(json.dumps(reports,indent=2));rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'))
assert all(v['skin_stretch_p99_max'][0]<2.0 for v in reports.values()),'Skin stretch gate failed'
assert all(v['skin_stretch_p99_max'][1]<4.5 for v in reports.values()),'Worst edge stretch gate failed'
