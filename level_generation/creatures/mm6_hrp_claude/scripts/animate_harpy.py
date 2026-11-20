"""Native-derived Harpy flight and talon attack; all transforms keep measured segment lengths."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;FPS=32;sc.render.fps=FPS
D=json.loads((P/'work/rig.json').read_text());B=D['bones'];R={n:rig.data.bones[n].matrix_local.copy() for n in B};REL={n:R[b['parent']].inverted()@R[n] if b['parent'] else R[n] for n,b in B.items()}
C=np.array([v.co[:] for v in body.data.vertices]);E=np.array([e.vertices[:] for e in body.data.edges]);PA=np.array([v.value for v in body.data.attributes['part'].data]);WING=np.load(P/'work/wing_mask.npy');EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1);USE=EL>1e-5
DUR={'Standing':1.125,'Walking':1.125,'Running':.875,'Attack':1.75,'Cast':1.625,'Hit':1.125,'Fidget':2.25,'Death':1.875,'Dead':1.}
ROLES=list(DUR)
def ss(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
def env(t,a,b,c):return ss((t-a)/(b-a))*(1-ss((t-b)/(c-b)))
def rot(a,axis):return Matrix.Rotation(float(a),3,axis)
def mat(r,p):m=r.to_4x4();m.translation=Vector(p);return m
def norm(v):return np.asarray(v)/max(np.linalg.norm(v),1e-9)
def pose(role,t):
 if role=='Dead':role,t='Death',DUR['Death']
 cycle=DUR[role] if role in ['Standing','Walking','Running'] else DUR[role]/round(DUR[role]/1.125)
 phase=2*math.pi*t/cycle;gait=role in ['Walking','Running'];run=role=='Running';attack=role=='Attack';cast=role=='Cast'
 chamber=env(t,.32,.96,1.32) if attack else env(t,.20,.84,1.16)*.55 if cast else 0.
 kick=env(t,1.0,1.22,1.68) if attack else 0.
 attackLean=env(t,.65,1.18,1.68) if attack else 0.
 release=env(t,.84,1.10,1.56) if cast else 0.
 hit=env(t,0,.22,1.06) if role in ['Hit','Death'] else 0.
 fall=ss((t-.24)/1.46) if role=='Death' else 0.
 fidget=env(t,.25,.9,2.1) if role=='Fidget' else 0.
 pitch=(.08 if gait else .012)*math.sin(phase)*(.25 if gait else 1)+(.12 if gait else 0)+(.08 if run else 0)-.20*chamber+.13*kick-.13*hit+.1*release
 pitch-=.28*attackLean
 yaw=.012*math.sin(phase)
 rootrot=rot(pitch*(1-fall),'X')@rot(math.pi/2*fall+.14*attackLean,'Y')@rot(yaw*(1-fall),'Z')
 hips=Vector(B['Hips']['head']);offset=Vector((.012*math.sin(phase)*(1-fall),(.035*chamber-.04*kick)*(1-fall),.013*(1-math.cos(phase))*(1-fall)-.78*fall))
 M={'Root':mat(rootrot@R['Root'].to_3x3(),hips+offset-rootrot@hips)}
 for n,b in B.items():
  if n=='Root':continue
  m=M[b['parent']]@REL[n]
  if n in ['Spine','Spine1','Spine2','Neck','Head']:
   carry=rootrot
   angle=(-.04*chamber+.035*kick-.04*hit+.04*release) if n.startswith('Spine') else .04*chamber-.04*kick+.05*hit-.12*release if n=='Head' else 0
   turn=.24*fidget if n=='Head' else .05*math.sin(phase)*(1-fall) if n=='Neck' else 0
   m=mat(carry@rot(angle,'X')@rot(turn,'Z')@carry.transposed()@m.to_3x3(),m.translation)
  M[n]=m
 carrier=M['Spine2']@R['Spine2'].inverted();cr=carrier.to_3x3()
 def solve_pair(un,fn,hn,target,pole,carry):
  a=np.linalg.norm(np.array(B[fn]['head'])-B[un]['head']);b=np.linalg.norm(np.array(B[hn]['head'])-B[fn]['head']);start=np.array(M[un].translation);v=np.array(target)-start;dist=np.clip(np.linalg.norm(v),abs(a-b)+.003,a+b-.002);axis=norm(v);target=start+axis*dist
  po=np.array(pole)-start;po=norm(po-axis*(po@axis));along=(a*a-b*b+dist*dist)/(2*dist);joint=start+axis*along+po*math.sqrt(max(0,a*a-along*along))
  for n,h,tip,resttip in [(un,start,joint,B[fn]['head']),(fn,joint,target,B[hn]['head'])]:
   orig=carry@Vector(np.array(resttip)-B[n]['head']);q=orig.rotation_difference(Vector(tip-h));M[n]=mat(q.to_matrix()@carry@R[n].to_3x3(),h)
  return Vector(target)
 for sd,sg in [('L',1),('R',-1)]:
  un,fn,hn=[sd+x for x in ['Arm','ForeArm','Hand']];restW=Vector(B[hn]['head']);restE=Vector(B[fn]['head'])
  shift=Vector((-sg*.15, -.012,.005))+Vector((sg*(.075*chamber+.13*release),-.075*chamber-.20*release,.16*chamber+.33*release))
  shift+=Vector((sg*.012*math.sin(phase),.014*math.sin(phase+(0 if sg==1 else math.pi)),.012*math.sin(phase)))
  if sd=='R':shift+=Vector((-.015*hit,-.16*hit,.56*hit))
  else:shift+=Vector((.10*hit,0,.11*hit))
  if fall:shift=shift.lerp(Vector((-sg*.40,-.17,.13)),fall)
  target=solve_pair(un,fn,hn,carrier@(restW+shift),carrier@restE+cr@Vector((sg*.08,.075,0)).lerp(Vector((-sg*.60,-.35,.08)),fall),cr)
  delta=M[fn].to_3x3()@R[fn].to_3x3().transposed();handrot=delta@R[hn].to_3x3()
  if fall:handrot=handrot.to_quaternion().slerp((cr@rot(sg*.8,'Y')@R[hn].to_3x3()).to_quaternion(),fall).to_matrix()
  M[hn]=mat(handrot,target)
  for d in [x for x in D['digits'] if x['kind']=='hand' and x['side']==sd]:
   for n in d['names']:
    m=M[B[n]['parent']]@REL[n];amount=.045+.07*chamber+.06*hit+.10*fall-.025*release
    # Curl axis follows each palm's sideways normal, avoiding forearm roll.
    local=R[n].to_3x3().transposed()@Vector((0,sg,0));M[n]=m@Matrix.Rotation(amount,4,local)
 # Avian legs: two-bone hip/knee solve to the hock; the tarsus and foot preserve their own directions.
 hipcarry=M['Hips']@R['Hips'].inverted();hr=hipcarry.to_3x3()
 for sd,sg in [('L',1),('R',-1)]:
  un,fn,tn,ft=[sd+x for x in ['Thigh','Shin','Tarsus','Foot']]
  restA=Vector(B[ft]['head']);restH=Vector(B[tn]['head']);restK=Vector(B[fn]['head'])
  offset=Vector((sg*(.09*chamber+.045*kick),-.26*chamber-.80*kick,.48*chamber+.54*kick))
  offset+=Vector((0,.014*math.sin(phase+(0 if sg>0 else math.pi)),.006*(1-math.cos(phase))))
  if sd=='R':offset+=Vector((-.06*hit,-.22*hit,.24*hit))
  if fall:offset=offset.lerp(Vector((-sg*.10,-.035,.05 if sg>0 else .16)),fall)
  footpitch=-.35*chamber-1.17*kick-.15*hit
  footrot=hr@rot(footpitch,'X');ankle=hipcarry@(restA+offset);hock=ankle-footrot@(restA-restH)
  # Carry the knee guide with the hip-to-hock direction so the kick cannot cross its pole.
  restHip=Vector(B[un]['head']);start=M[un].translation
  turn=(hr@(restH-restHip)).rotation_difference(hock-start)
  pole=start+turn@(hr@(restK-restHip+Vector((sg*(.025+.18*chamber),-.25,0))))
  hock=solve_pair(un,fn,tn,hock,pole,hr)
  ankle=hock+footrot@(restA-restH);M[tn]=mat(footrot@R[tn].to_3x3(),hock);M[ft]=mat(footrot@R[ft].to_3x3(),ankle)
  for d in [x for x in D['digits'] if x['kind']=='foot' and x['side']==sd]:
   n=d['names'][0];M[n]=M[ft]@REL[n]@Matrix.Rotation(.08*chamber-.035*kick+.12*fall,4,'X')
 for sd,sg in [('L',1),('R',-1)]:
  for k in range(3):
   n=sd+'Wing'+str(k);m=M[B[n]['parent']]@REL[n]
   flap=(.16-(.52 if run else .44)*math.cos(phase)) if k==0 else -.08*math.cos(phase-.6) if k==1 else -.065*math.cos(phase-1.2)
   flap+=(-.12*chamber+.16*kick-.10*release) if k==0 else .05*kick
   delta=cr@rot(sg*flap,'Y')@rot(sg*.045*math.sin(phase-k*.4),'Z')@cr.transposed();live=delta@m.to_3x3()
   if fall:
    # Fold the wings onto a horizontal plane while the body falls back onto its side.
    flat=rot(sg*(-.60-.30*k),'Z')@rot(-math.pi/2,'X')@R[n].to_3x3();live=live.to_quaternion().slerp(flat.to_quaternion(),fall).to_matrix()
   M[n]=mat(live,m.translation)
 for k in range(2):
  n='Tail'+str(k);m=M[B[n]['parent']]@REL[n];m=m@Matrix.Rotation((.045*math.sin(phase-.5*k)+.10*chamber)*(1-fall),4,'X')
  M[n]=m
 for n,b in B.items():
  basis=REL[n].inverted()@(M[b['parent']].inverted()@M[n] if b['parent'] else M[n]);rig.pose.bones[n].matrix_basis=basis
 bpy.context.view_layer.update()
 deps=bpy.context.evaluated_depsgraph_get();obj=body.evaluated_get(deps);mesh=obj.to_mesh();pts=np.array([v.co[:] for v in mesh.vertices]);obj.to_mesh_clear()
 # Root correction enforces actual surface contact. Wings are separately flattened during death.
 z=pts[:,2].min()
 if z<0:rig.pose.bones['Root'].location+=R['Root'].to_3x3().transposed()@Vector((0,0,-float(z)));bpy.context.view_layer.update()
 return {'chamber':chamber,'kick':kick,'fall':fall}
rig.animation_data_clear()
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
reports={};traces={}
masks={'all':np.ones(len(C),dtype=bool),'wing':WING,'hand':(C[:,2]<.91)&(abs(C[:,0])>.44),'arm':(C[:,2]>.9)&(C[:,2]<1.42)&(abs(C[:,0])>.23)&~WING,'leg':(C[:,2]<1.01)&(abs(C[:,0])<.4),'body':(~WING)&(C[:,2]>1.0)&(abs(C[:,0])<.23)}
for role in ROLES:
 action=bpy.data.actions.new(role);action.use_fake_user=True;count=round(DUR[role]*FPS);keys={n:[] for n in B};worst={k:[] for k in masks};mins=[];first=None;last=None;trace=[]
 for frame in range(count+1):
  rig.animation_data_clear();intent=pose(role,frame/FPS);obj=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh();c=np.array([v.co[:] for v in mesh.vertices]);obj.to_mesh_clear();first=c.copy() if first is None else first;last=c;stretch=np.linalg.norm(c[E[:,1]]-c[E[:,0]],axis=1)/np.maximum(EL,1e-8);mins.append(float(c[:,2].min()))
  for k,mask in masks.items():
   a=stretch[USE&mask[E[:,0]]&mask[E[:,1]]];worst[k].append([float(np.percentile(a,99)),float(a.max())])
  trace.append({'time':frame/FPS,'left_talon':list(rig.pose.bones['LToe1'].tail),'right_talon':list(rig.pose.bones['RToe1'].tail),**intent})
  for n in B:
   pb=rig.pose.bones[n];q=pb.rotation_quaternion.copy()
   if keys[n] and q.dot(keys[n][-1][1])<0:q.negate()
   keys[n].append((pb.location.copy(),q))
 rig.animation_data_create();rig.animation_data.action=action
 for frame in range(count+1):
  for n in B:
   pb=rig.pose.bones[n];pb.location,pb.rotation_quaternion=keys[n][frame];pb.keyframe_insert('location',frame=frame+1,group=n);pb.keyframe_insert('rotation_quaternion',frame=frame+1,group=n)
 for layer in action.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 report={'duration':count/FPS,'min_z':min(mins),'loop_delta':float(np.linalg.norm(last-first,axis=1).max()),'stretch':{p:np.max(a,axis=0).tolist() for p,a in worst.items()}};reports[role]=report;traces[role]=trace;print(role,json.dumps(report),flush=True)
 assert report['min_z']>-.002
 if role in ['Standing','Walking','Running','Dead']:assert report['loop_delta']<.002,(role,report['loop_delta'])
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
(P/'work/animation_audit.json').write_text(json.dumps(reports,indent=2));(P/'work/motion_traces.json').write_text(json.dumps(traces,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'))
