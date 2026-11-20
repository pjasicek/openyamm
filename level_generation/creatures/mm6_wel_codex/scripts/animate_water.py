"""Native tail glide, trident windup/sweep, library recoil and sinking death."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_prop.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=60
D=json.loads((P/'work/rig.json').read_text());B=D['bones'];R={n:rig.data.bones[n].matrix_local.copy() for n in B};REL={n:R[b['parent']].inverted()@R[n] if b['parent'] else R[n] for n,b in B.items()};J={n:Vector(v) for n,v in D['joints'].items()};T=np.array(D['tail']['joints']);K=D['tail']['root_index'];L=np.linalg.norm(np.diff(T,axis=0),axis=1);GR=json.loads((P/'work/grip_pose.json').read_text());SRC=json.loads((P/'work/source_rest.json').read_text());SOURCE=json.loads((P/'work/source_motion.json').read_text())['UnarmedGetHitF2']
C=np.array([v.co[:] for v in body.data.vertices]);E=np.array([e.vertices[:] for e in body.data.edges]);PA=np.array([v.value for v in body.data.attributes['part'].data]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1)
DURS={'Standing':3.,'Walking':1.125,'Running':.85,'Attack':1.35,'Cast':1.4,'Hit':1.125,'Fidget':3.,'Death':1.125,'Dead':1.}
def ss(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
def env(t,a,b,c):return ss((t-a)/(b-a))*(1-ss((t-b)/(c-b)))
def qrot(axis,a):return Quaternion(axis,a)
def mat(rot,p):m=rot.to_matrix().to_4x4() if isinstance(rot,Quaternion) else rot.to_4x4();m.translation=Vector(p);return m
def frame(a,b):
 a=Vector(a).normalized();b=Vector(b);b=(b-a*a.dot(b)).normalized();return Matrix((a,b,a.cross(b))).transposed()
def align(a,b,c,d):return frame(c,d)@frame(a,b).transposed()
def path(t,keys):
 if t<=keys[0][0]:return Vector(keys[0][1])
 for (a,p),(b,q) in zip(keys,keys[1:]):
  if t<=b:return Vector(p).lerp(Vector(q),ss((t-a)/(b-a)))
 return Vector(keys[-1][1])
def swingtwist(q):
 v=Vector((0,q.y,0));tw=Quaternion((q.w,0,q.y,0));tw.normalize();sw=q@tw.inverted();s=min(sw.angle,2*math.pi-sw.angle);t=(2*math.atan2(q.y,q.w)+math.pi)%(2*math.pi)-math.pi;return s,t
prev_phi=None;prev_pole=None

def pose(role,t):
 global prev_phi,prev_pole
 if role=='Dead':role,t='Death',DURS['Death']
 cyc=2*math.pi*t/DURS[role];gait=role in ('Walking','Running');attack=role=='Attack';cast=role=='Cast';death=role=='Death';hit=env(t,0,.19,1.125) if role=='Hit' else 0
 wind=env(t,0,.47,.90) if attack or cast else 0;strike=env(t,.57,1.02,DURS[role]) if attack or cast else 0;burst=env(t,0,.24,.58) if death else 0;fall=ss((t-.27)/.855) if death else 0;fidget=math.sin(cyc)*math.sin(cyc*.5)**2 if role=='Fidget' else 0
 pitch=(.13 if gait else .016*math.sin(cyc))-.17*wind+.22*strike-.16*hit-.12*burst
 yaw=.06*fidget-.12*wind+.16*strike;bank=-.035*wind+.035*strike
 pts=T.copy();pts[K]+=np.array([0,0,.006*math.sin(cyc)])
 for i in list(range(K-1,-1,-1))+list(range(K,len(L))):
  up=i<K;v=Vector(T[i]-T[i+1] if up else T[i+1]-T[i]);u=(K-i)/K if up else (i-K)/max(1,len(L)-K-1)
  if up:
   v=qrot((0,0,1),yaw*u)@qrot((0,1,0),bank*u)@qrot((1,0,0),pitch*u)@v
   pts[i]=pts[i+1]+np.array(v)
  else:
   theta=math.atan2(v.z,v.y)*(1-u)+u*(.05+(.37 if gait else .035)*math.sin(cyc-u*2.5));side=.05*math.sin(cyc-u*2)*u if gait else 0
   v=Vector((side,math.cos(theta),math.sin(theta))).normalized()*L[i];pts[i+1]=pts[i]+np.array(v)
 M={'Root':R['Root'].copy()};M['Root'].translation=Vector(pts[K])
 for i in range(len(L)):
  n=f'Serpent_{i:02}';a,b=(pts[i+1],pts[i]) if i<K else (pts[i],pts[i+1]);delta=Vector(np.array(B[n]['tail'])-np.array(B[n]['head'])).rotation_difference(Vector(b-a));M[n]=mat(delta@R[n].to_quaternion(),a)
 k=min(max(t-.08,0),.5)*30;ki=min(int(k),len(SOURCE['keys'])-1);kj=min(ki+1,len(SOURCE['keys'])-1)
 def source_delta(n):return Quaternion(SOURCE['keys'][ki][n]['q']).slerp(Quaternion(SOURCE['keys'][kj][n]['q']),k-ki)@Matrix(SRC[n]['rot']).to_quaternion().inverted()
 for n,b in B.items():
  if n in M:continue
  m=M[b['parent']]@REL[n]
  if n.startswith('B_Spine'):
   add=-.045*wind+.045*strike-.03*burst
   m=mat(qrot((1,0,0),add)@qrot((0,0,1),(-.035*wind+.055*strike))@m.to_quaternion(),m.translation)
   if role=='Hit':m=mat((M['B_Pelvis'].to_quaternion()@R['B_Pelvis'].to_quaternion().inverted())@Quaternion().slerp(source_delta(n),.40*hit)@R[n].to_quaternion(),m.translation)
  if n=='B_Head':m=mat(qrot((0,0,1),.28*fidget+.14*wind-.18*strike)@qrot((1,0,0),-.04*wind-.07*hit)@m.to_quaternion(),m.translation)
  M[n]=m
 X=M['B_Spine2']@R['B_Spine2'].inverted();cr=X.to_3x3()
 # The right palm tunnel is aligned to the actual trident line; solve the entire arm around it.
 idleG=Vector((-.37,-.265,1.075));idleA=Vector((0,-.83,.56));G=idleG.copy();A=idleA.copy();pole=Vector((-.51,.10,1.36))
 if attack or cast:
  G=path(t,[(0,idleG),(.47,(-.53,-.07,1.29)),(.64,(-.68,-.07,1.66)),(.82,(-.48,-.23,1.70)),(.94,(-.28,-.37,1.35)),(1.02,(-.28,-.43,1.07)),(DURS[role],idleG)])
  A=path(t,[(0,idleA),(.47,(-.10,.12,.99)),(.64,(-.60,.30,.74)),(.82,(.15,-.5,.85)),(.94,(.75,-.48,-.05)),(1.02,(.85,-.38,-.36 if attack else .12)),(DURS[role],idleA)])
  pole=path(t,[(0,pole),(.47,(-.47,.13,1.35)),(.64,(-.55,.06,1.58)),(1.02,(-.41,.02,1.27)),(DURS[role],pole)])
 if gait:G+=Vector((-.01,-.025,.025*math.sin(cyc)));A+=Vector((0,.04*math.sin(cyc),.02*math.cos(cyc)))
 if hit:G=G.lerp(Vector((-.53,-.25,1.55)),hit);A=A.lerp(Vector((-.15,.25,.96)),hit)
 if death:G=G.lerp(Vector((-.48,-.13,1.48)),burst);A=A.lerp(Vector((0,0,1)),max(burst,fall))
 G+=Vector((-.02*abs(fidget),-.04*abs(fidget),.04*fidget));A+=Vector((.035*fidget,0,0));G=X@G;A=(cr@A).normalized();pole=X@pole
 un,fn,hn=['B_R_'+s for s in ('UpperArm','Forearm','Hand')];S=M[un].translation;a=(J['R_Forearm']-J['R_UpperArm']).length;b=(J['R_Hand']-J['R_Forearm']).length;gh=Vector(GR['handle_centre_hand_local']);ah=Vector(GR['handle_axis_hand_local']);q0=(R[hn].to_3x3()@ah).rotation_difference(A).to_matrix();rn=(J['R_Forearm']-J['R_UpperArm']).cross(J['R_Hand']-J['R_Forearm'])
 def solve(phi,pa):
  Rh=qrot(A,phi).to_matrix()@q0@R[hn].to_3x3();W=G-Rh@gh;v=W-S;dist=min(max(v.length,abs(a-b)+.005),a+b-.005);v.normalize();W2=S+v*dist;pp=pole-S;pp=(pp-v*v.dot(pp)).normalized();pp=qrot(v,pa)@pp;al=(a*a-b*b+dist*dist)/(2*dist);el=S+v*al+pp*math.sqrt(max(0,a*a-al*al));wn=(el-S).cross(W2-el)
  Ra=align(J['R_Forearm']-J['R_UpperArm'],rn,el-S,wn)@R[un].to_3x3();Rf=align(J['R_Hand']-J['R_Forearm'],rn,W2-el,wn)@R[fn].to_3x3();expected=Rf@R[fn].to_3x3().transposed()@R[hn].to_3x3();_,tw=swingtwist((expected.transposed()@Rh).to_quaternion());ft=max(-1.4,min(1.4,tw*.8));Rf=qrot((W2-el).normalized(),ft).to_matrix()@Rf;expected=Rf@R[fn].to_3x3().transposed()@R[hn].to_3x3();sw,tw=swingtwist((expected.transposed()@Rh).to_quaternion());miss=(W-W2).length
  cost=sw+.8*abs(tw)+.12*abs(ft)+miss*40+.035*abs(pa)+max(0,el.x+.20)*10+5*max(0,sw-math.radians(50))**2
  if prev_pole is not None:cost+=.10*abs(pa-prev_pole)
  if prev_phi is not None:cost+=.12*abs((phi-prev_phi+math.pi)%(2*math.pi)-math.pi)
  return cost,phi,Ra,Rf,Rh,el,W2,sw,tw,miss,pa
 best=min((solve(phi,pa) for phi in np.linspace(-math.pi,math.pi,49)[:-1] for pa in np.radians(np.arange(-90,91,15))),key=lambda x:x[0]);best=min((solve(best[1]+math.radians(d),best[-1]+math.radians(a)) for d in np.arange(-7.5,7.6,1.5) for a in [-7.5,-3,0,3,7.5]),key=lambda x:x[0]);_,prev_phi,Ra,Rf,Rh,el,W2,sw,tw,miss,prev_pole=best
 if attack or cast:
  # Keep an anatomical elbow plane and derive the prop direction from a bounded wrist.
  W=X@path(t,[(0,(-.465,-.163,1.148)),(.47,(-.60,-.20,1.45)),(.70,(-.52,-.13,1.61)),(.86,(-.43,-.28,1.62)),(1.02,(-.32,-.35,1.13)),(DURS[role],(-.465,-.163,1.148))])
  pole=X@path(t,[(0,(-.59,.04,1.30)),(.47,(-.72,.05,1.35)),(.70,(-.72,-.03,1.39)),(.86,(-.63,-.06,1.40)),(1.02,(-.46,.01,1.26)),(DURS[role],(-.59,.04,1.30))])
  v=W-S;dist=min(max(v.length,abs(a-b)+.005),a+b-.005);v.normalize();W2=S+v*dist;pp=pole-S;pp=(pp-v*v.dot(pp)).normalized();al=(a*a-b*b+dist*dist)/(2*dist);el=S+v*al+pp*math.sqrt(max(0,a*a-al*al));wn=(el-S).cross(W2-el)
  Ra=align(J['R_Forearm']-J['R_UpperArm'],rn,el-S,wn)@R[un].to_3x3();Rf=align(J['R_Hand']-J['R_Forearm'],rn,W2-el,wn)@R[fn].to_3x3()
  natural=(cr@(J['R_Forearm']-J['R_UpperArm'])).rotation_difference(el-S).to_matrix()@cr@R[un].to_3x3();_,st=swingtwist((natural.transposed()@Ra).to_quaternion());Ra=natural@qrot((0,1,0),max(-1.05,min(1.05,st))).to_matrix()
  neutral=Rf@R[fn].to_3x3().transposed()@R[hn].to_3x3();fore_y=(W2-el).normalized();desired=(A-fore_y*A.dot(fore_y)).normalized();actual=neutral@ah;actual=(actual-fore_y*actual.dot(fore_y)).normalized();twist=math.radians(path(t,[(0,(46,0,0)),(.47,(65,0,0)),(.72,(70,0,0)),(.85,(45,0,0)),(1.02,(-65,0,0)),(1.13,(-55,0,0)),(DURS[role],(46,0,0))]).x);Rf=qrot(fore_y,twist).to_matrix()@Rf
  neutral=Rf@R[fn].to_3x3().transposed()@R[hn].to_3x3();delta=(neutral@ah).rotation_difference(A);Rh=Quaternion().slerp(delta,min(1,math.radians(35)/max(delta.angle,1e-6))).to_matrix()@neutral
  # Blend the attack ends into the exact idle wrist and elbow transforms.
  fade=ss(t/.22)*ss((DURS[role]-t)/.22)
  if fade<1:
   base=best;Ra=base[2].to_quaternion().slerp(Ra.to_quaternion(),fade).to_matrix();el=base[5].lerp(el,fade);Rf=base[3].to_quaternion().slerp(Rf.to_quaternion(),fade).to_matrix();W2=base[6].lerp(W2,fade);Rh=base[4].to_quaternion().slerp(Rh.to_quaternion(),fade).to_matrix()
  expected=Rf@R[fn].to_3x3().transposed()@R[hn].to_3x3();sw,tw=swingtwist((expected.transposed()@Rh).to_quaternion());miss=0.
 M[un]=mat(Ra,S);M[fn]=mat(Rf,el);M[hn]=mat(Rh,W2)
 for f in range(5):
  for n in [f'B_R_Finger{f}'+suffix for suffix in ('','1','2')]:M[n]=M[B[n]['parent']]@REL[n]@Quaternion(GR['finger_local'][n]).to_matrix().to_4x4()
 # Free left hand counterbalances the strike and opens during hit/death.
 un,fn,hn=['B_L_'+s for s in ('UpperArm','Forearm','Hand')];S=M[un].translation;idle=Vector((.455,-.09,1.06));W=idle+Vector((.005*math.sin(cyc),-.014*math.sin(cyc),.012*math.sin(cyc)));pole=Vector((.50,.12,1.32))
 if attack or cast:W=path(t,[(0,idle),(.47,(.55,.01,1.36)),(.64,(.55,-.03,1.39)),(1.02,(.30,-.24,1.19)),(DURS[role],idle)])
 if hit:W=W.lerp(Vector((.44,-.12,1.59)),hit)
 if death:W=W.lerp(Vector((.55,-.10,1.59)),max(burst,.7*fall))
 W+=Vector((0,-.035*fidget,.08*fidget));W=X@W;pole=X@pole;a=(J['L_Forearm']-J['L_UpperArm']).length;b=(J['L_Hand']-J['L_Forearm']).length;v=W-S;dist=min(max(v.length,abs(a-b)+.005),a+b-.005);v.normalize();W=S+v*dist;pp=pole-S;pp=(pp-v*v.dot(pp)).normalized();al=(a*a-b*b+dist*dist)/(2*dist);el=S+v*al+pp*math.sqrt(max(0,a*a-al*al));rn=(J['L_Forearm']-J['L_UpperArm']).cross(J['L_Hand']-J['L_Forearm']);wn=(el-S).cross(W-el)
 for n,start,end,rstart,rend in [(un,S,el,J['L_UpperArm'],J['L_Forearm']),(fn,el,W,J['L_Forearm'],J['L_Hand'])]:M[n]=mat(align(rend-rstart,rn,end-start,wn)@R[n].to_3x3(),start)
 M[hn]=mat(M[fn].to_3x3()@R[fn].to_3x3().transposed()@R[hn].to_3x3(),W)
 for f in range(5):
  for n in [f'B_L_Finger{f}'+s for s in ('','1','2')]:M[n]=M[B[n]['parent']]@REL[n]@Matrix.Rotation(-.09-.035*math.sin(cyc+f)+.09*max(hit,burst),4,'X')
 for n in ['Trident','Socket_Trident_Head']:M[n]=M[B[n]['parent']]@REL[n]
 for sd in ('L','R'):
  n='Fin_'+sd;M[n]=M['B_Pelvis']@REL[n]@Matrix.Rotation(.045*math.sin(cyc+(.5 if sd=='L' else 0))+.055*strike,4,'Y')
 M['Hair']=M['B_Head']@REL['Hair']@Matrix.Rotation(.025*math.sin(cyc-.6)+.08*strike-.06*wind,4,'X')
 for n,bone in B.items():
  par=bone['parent'];rig.pose.bones[n].matrix_basis=REL[n].inverted()@(M[par].inverted()@M[n] if par else M[n])
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(v.co.z for v in me.vertices);ev.to_mesh_clear();lift=.008-low
 rig.pose.bones['Root'].location+=R['Root'].to_3x3().transposed()@Vector((0,0,lift-4.4*fall));bpy.context.view_layer.update()
 return {'wrist_swing':math.degrees(sw),'wrist_twist':math.degrees(tw),'grip_target_error':miss,'fall':fall}

rig.animation_data_clear()
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
pilot=False;roles=['Standing','Walking','Attack','Hit','Death','Dead'] if pilot else list(DURS);reports={}
for role in roles:
 prev_phi=None;prev_pole=None;count=int(DURS[role]*60+1e-8);keys={n:[] for n in B};metrics=[];stretch=[];first=None;mins=[]
 for f in range(count+1):
  rig.animation_data_clear();metrics.append(pose(role,f*DURS[role]/count));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();first=co.copy() if first is None else first;mins.append(float(co[:,2].min()));length=np.linalg.norm(co[E[:,1]]-co[E[:,0]],axis=1);rat=length/np.maximum(EL,1e-9);masks={'body':PA==0,'tail':PA==5,'hands':np.isin(PA,[1,6]),'head':np.isin(PA,[2,4,7,12,14])};stretch.append({n:[float(np.percentile(rat[m[E[:,0]]&m[E[:,1]]&(EL>.002)],99)),float(rat[m[E[:,0]]&m[E[:,1]]&(EL>.002)].max())] for n,m in masks.items()})
  for n in B:
   pb=rig.pose.bones[n];q=pb.rotation_quaternion.copy()
   if keys[n] and q.dot(keys[n][-1][1])<0:q.negate()
   keys[n].append((pb.location.copy(),q,pb.scale.copy()))
 a=bpy.data.actions.new(role);a.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=a
 for f in range(count+1):
  for n in B:
   pb=rig.pose.bones[n];pb.location,pb.rotation_quaternion,pb.scale=keys[n][f]
   for prop in ('location','rotation_quaternion','scale'):pb.keyframe_insert(prop,frame=f+1,group=n)
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 reports[role]={'duration':count/60,'loop_delta':float(np.linalg.norm(co-first,axis=1).max()),'min_z':min(mins),'wrist_swing':max(m['wrist_swing'] for m in metrics),'wrist_twist':max(abs(m['wrist_twist']) for m in metrics),'grip_target_error':max(m['grip_target_error'] for m in metrics),'wrist_worst_time':int(np.argmax([m['wrist_swing'] for m in metrics]))/60,'stretch':{n:np.max([r[n] for r in stretch],axis=0).tolist() for n in masks}};print(role,reports[role],flush=True)
 common.workbench_clay(sc)
 frames=[0,round(count*.2),round(count*.4),round(count*.6),round(count*.8),count] if role in ('Attack','Death') else [0,round(count*.33),round(count*.66)]
 for f in frames:
  sc.frame_set(f+1);common.render_views(str(P/'review'/f'clay_{role}_{f:03}'),1.35,3.4,views=('front','left'),resolution=(500,600),target=(0,-.2))
(P/'work/animation_audit.json').write_text(json.dumps(reports,indent=2));rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/('work/pilot_v1.blend' if pilot else 'work/anim_v1.blend')))
assert all(reports[n]['loop_delta']<.003 for n in ('Standing','Walking','Dead')),'Loop gate'
assert all(v['wrist_swing']<=60 and v['wrist_twist']<=60 for v in reports.values()),'Wrist gate'
assert all(v['stretch']['hands'][1]<4.5 and v['stretch']['body'][0]<2 for v in reports.values()),'Deformation gate'
