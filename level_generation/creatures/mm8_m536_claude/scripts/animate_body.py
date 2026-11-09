"""Native levitation and disappearance with owned source-frame dual-palm casting."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30
D=json.loads((P/'work/rig.json').read_text());B=D['bones'];R={n:rig.data.bones[n].matrix_local.copy() for n in B};REL={n:R[b['parent']].inverted()@R[n] if b['parent'] else R[n] for n,b in B.items()};SOURCES=json.loads((P/'work/source_motion.json').read_text());SRC=json.loads((P/'work/source_rest.json').read_text());C=np.array([v.co[:] for v in body.data.vertices]);E=np.array([e.vertices[:] for e in body.data.edges]);PA=np.array([v.value for v in body.data.attributes['part'].data]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1)
LOOPS={'Standing':1.75,'Walking':.9,'Running':.6,'Attack':1.5,'Cast':1.5,'Hit':.625,'Fidget':1.5,'Death':.75,'Dead':1.}
def ss(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
def env(t,a,b,c):return ss((t-a)/(b-a))*(1-ss((t-b)/(c-b)))
def matrix(q,p):m=q.to_matrix().to_4x4() if isinstance(q,Quaternion) else q.to_4x4();m.translation=Vector(p);return m
def rot(axis,angle):return Quaternion(axis,angle)
def setq(m,q):return matrix(q,m.translation)
# Crossed arms are fitted to reachable wrists in front of the native chest, with staggered forearms.
IDLE={}
for sd,sign in [('L',1),('R',-1)]:
 un,fn,hn=['B_'+sd+'_'+n for n in ['UpperArm','Forearm','Hand']]
 sh=R[un].translation;el=R[fn].translation;wr=R[hn].translation
 target=Vector((-sign*.12,-.40,2.20+(0.045 if sd=='L' else -.045)))
 a=(el-sh).length;b=(wr-el).length;v=target-sh;length=min(v.length,(a+b)*.98);direction=v.normalized()
 along=(a*a-b*b+length*length)/(2*length);pole=Vector((sign*.5,-.12,1.98))-sh;pole=(pole-direction*pole.dot(direction)).normalized()
 elbow=sh+direction*along+pole*math.sqrt(max(0,a*a-along*along));wrist=sh+direction*length
 IDLE[un]=(el-sh).rotation_difference(elbow-sh)@R[un].to_quaternion()
 IDLE[fn]=(wr-el).rotation_difference(wrist-elbow)@R[fn].to_quaternion()
 finger=Vector(B['B_'+sd+'_Finger2']['head'])-wr
 IDLE[hn]=finger.rotation_difference(Vector((-sign,.05,.12)))@R[hn].to_quaternion()
def pose(role,t):
 if role=='Dead':role,t='Death',LOOPS['Death']
 SOURCE=SOURCES['UnarmedCastDualSummon1' if role=='Cast' else 'UnarmedCastDualAttack1']
 cycle=2*math.pi*t/LOOPS[role];gait=role in ['Walking','Running'];run=role=='Running';action=role in ['Attack','Cast'];ct=t;wind=env(ct,0,.38,.76) if action else 0.;release=env(ct,.38,.78,1.45) if action else 0.;hit=env(t,0,.19,.625) if role=='Hit' else 0.;fidget=math.sin(cycle)*ss(t/.25)*(1-ss((t-2.15)/.25)) if role=='Fidget' else 0.;death=role=='Death';fall=ss(t/.70) if death else 0
 M={'Root':R['Root'].copy()}
 pitch=(-.12*wind+.17*release-.19*hit)+(.14 if run else .065 if gait else .012*math.sin(cycle));yaw=.08*wind-.055*release+.09*fidget;bank=.045*math.sin(cycle) if gait else -.07*wind+.06*release
 q=rot((0,0,1),yaw)@rot((0,1,0),bank)@rot((1,0,0),pitch-.35*fall)
 root=R['BodyRoot'].translation+Vector((.025*math.sin(cycle) if gait else -.035*wind+.045*release, .045*wind-.055*release,.025*math.sin(cycle)*(1-fall)))
 root.z-=1.53*fall
 scale=max(.0001,1-ss((t-.15)/.52)) if death else 1.
 M['BodyRoot']=matrix(q@R['BodyRoot'].to_quaternion(),root)@Matrix.Diagonal((scale,scale,scale,1))
 # Casting source clock retains its 30-Hz release/follow-through, preceded by a short ready blend.
 source_t=float(np.interp(ct,[0,.30,.95,1.25,LOOPS[role]],[0,.27,.31,.55,.55])) if action else 0
 k=source_t*30;i=min(int(k),len(SOURCE['keys'])-1);j=min(i+1,len(SOURCE['keys'])-1);blend=1. if action else 0.
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
   base=q@IDLE[n]
   if fall:base=base.slerp(q@R[n].to_quaternion(),fall)
   target=q@sq(n) if action else base;poseq=base.slerp(target,blend);m=setq(m,poseq)@Matrix.Diagonal((scale,scale,scale,1))
  elif '_Finger' in n:
   curl=.06+.12*wind-.05*release+.09*hit
   m=m@Matrix.Rotation(max(0,curl),4,'X')
  M[n]=m
 # Native attack frames begin with open arms; the runtime owns transitions between the hover and casting clips.
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
 count=math.ceil(dur*30);keys={n:[] for n in B};mins=[];ratio=[];first=None
 for f in range(count+1):
  rig.animation_data_clear();pose(role,f*dur/count);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();first=c.copy() if first is None else first;mins.append(float(c[:,2].min()));stretch=np.linalg.norm(c[E[:,1]]-c[E[:,0]],axis=1)/np.maximum(EL,1e-9);mask=(PA[E[:,0]]==0)&(PA[E[:,1]]==0)&(EL>1e-4);ratio.append([float(np.percentile(stretch[mask],99)),float(stretch[mask].max())])
  for n in B:
   pb=rig.pose.bones[n];qq=pb.rotation_quaternion.copy()
   if keys[n] and qq.dot(keys[n][-1][1])<0:qq.negate()
   keys[n].append((pb.location.copy(),qq,pb.scale.copy()))
 action=bpy.data.actions.new(role);action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action
 for f in range(count+1):
  for n in B:
   pb=rig.pose.bones[n];pb.location,pb.rotation_quaternion,pb.scale=keys[n][f]
   for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=1+f*dur*30/count,group=n)
 for layer in action.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 reports[role]={'duration':dur,'min_z':min(mins),'skin_stretch_p99_max':np.max(ratio,axis=0).tolist(),'loop_delta':float(np.linalg.norm(c-first,axis=1).max())};print(role,reports[role])
 common.workbench_clay(sc)
 for f in [0,round(count*.25),round(count*.5),round(count*.75),count]:
  sc.frame_set(1+int(f*dur*30/count),subframe=(f*dur*30/count)%1);common.render_views(str(P/'review'/f'clay_{role}_{f:03}'),2.2,2.0,views=('front','three_quarter'),resolution=(400,540))
(P/'work/animation_audit.json').write_text(json.dumps(reports,indent=2));rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'))
assert all(v['skin_stretch_p99_max'][0]<2.0 for v in reports.values()),'Skin stretch gate failed'
assert all(v['skin_stretch_p99_max'][1]<4.5 for v in reports.values()),'Worst edge stretch gate failed'
