"""Native-derived Medusa choreography, with measured-length serpent and analytic arm posing."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30
D=json.loads((P/'work/rig.json').read_text());J0=np.array(D['tail']['joints']);K=D['tail']['root_index'];L=np.linalg.norm(np.diff(J0,axis=0),axis=1);B=D['bones'];R={n:rig.data.bones[n].matrix_local.copy() for n in B};REL={n:R[b['parent']].inverted()@R[n] if b['parent'] else R[n] for n,b in B.items()};FPS=30
C=np.array([v.co[:] for v in body.data.vertices]);E=np.array([e.vertices[:] for e in body.data.edges]);PART=np.array([v.value for v in body.data.attributes['part'].data]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1);USE=EL>1e-5
LOOPS={'Standing':3.,'Walk':.9,'Running':2/3,'Fidget':2.4,'Attack':38/30,'Cast':1.5,'Hit':22/30,'Death':1.6,'Dead':1.}
def ss(x):x=np.clip(x,0,1);return float(x*x*(3-2*x))
def env(t,start,peak,end):return ss((t-start)/(peak-start))*(1-ss((t-peak)/(end-peak)))
def norm(v):return v/max(np.linalg.norm(v),1e-9)
def rx(a):return Matrix.Rotation(a,3,'X')
def matrix(rot,p):m=rot.to_4x4();m.translation=Vector(p);return m
def pose(role,t):
 if role=='Dead':role,t='Death',LOOPS['Death']
 if role=='Cast':role,t='Attack',min(t,LOOPS['Attack'])
 cyc=2*math.pi*t/LOOPS[role];gait=role in ['Walk','Running'];fall=ss((t-.28)/1.15) if role=='Death' else 0.;hit=env(t,0,.16,.7) if role=='Hit' else env(t,0,.2,.65)*.55 if role=='Death' else 0.;gaze=env(t,.04,.75,1.22) if role=='Attack' else 0.;cast=env(t,0,.75,1.46) if role=='Cast' else 0.;fidget=math.sin(cyc)*ss(t/.3)*(1-ss((t-2.1)/.3)) if role=='Fidget' else 0.
 windup=env(t,0,.36,.70) if role=='Attack' else 0.
 release=env(t,.40,.75,1.22) if role=='Attack' else 0.
 follow=env(t,.42,.84,1.24) if role=='Attack' else 0.
 side=.13*windup-.085*follow
 pitch=.018*math.sin(cyc) if role=='Standing' else -.12*hit-.12*windup+.19*release
 wave=.008 if role=='Standing' else (.74 if role=='Running' else .56) if gait else .025
 pts=J0.copy();pts[K]+=np.array([.005*math.sin(cyc) if gait else 0,0,0])
 for i in list(range(K-1,-1,-1))+list(range(K,len(J0)-1)):
  upward=i<K;d=Vector(J0[i]-J0[i+1] if upward else J0[i+1]-J0[i]);d.normalize();u=(K-i)/K if upward else (i-K)/(len(L)-K)
  if upward:
   angle=pitch*u+fall*1.35*(.55+.45*u);yaw=((.075 if role=='Running' else .058) if gait else .012)*math.sin(cyc-u*3)*(1-fall)+fall*1.5*u+side*u;d=Matrix.Rotation(yaw,3,'Y')@rx(angle)@d
   d.z*=1-fall;d.normalize();nxt=pts[i+1]+L[i]*np.array(d)
   # The collapsing front lies on its belly; preserve segment length at floor contact.
   floor=.145
   if fall and nxt[2]<floor:
    dz=np.clip(floor-pts[i+1,2],-L[i]*.95,L[i]*.95);h=norm(np.array([d.x,d.y,0]));nxt=pts[i+1]+h*math.sqrt(L[i]**2-dz**2)+[0,0,dz]
   pts[i]=nxt
  else:
   yaw=wave*math.sin(cyc-u*5.0)*(.3+.7*u)+fall*.45*u;d=Matrix.Rotation(yaw,3,'Z')@d;pts[i+1]=pts[i]+L[i]*np.array(d)
 M={'Root':R['Root'].copy()};M['Root'].translation=Vector(pts[K])
 for i in range(len(L)):
  n=f'Serpent_{i:02d}';a,b=(pts[i+1],pts[i]) if i<K else (pts[i],pts[i+1]);old=Vector(np.array(B[n]['tail'])-np.array(B[n]['head']));rot=old.rotation_difference(Vector(b-a)).to_matrix()@R[n].to_3x3();M[n]=matrix(rot,a)
 for n,b in B.items():
  if n in M:continue
  parent=b['parent'];m=M[parent]@REL[n]
  if n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
   ang=(.30*fall-.10*hit-.035*windup+.045*release) if n=='B_Spine' else .12*fall-.035*hit-.025*windup+.035*release if n.startswith('B_Spine') else (-.07*windup+.035*release+.08*hit-.05*fall) if n=='B_Head' else 0
   # Rotate in the carried body frame, not in the source bone's arbitrary local axes.
   if ang:m=matrix((M['B_Pelvis'].to_3x3()@R['B_Pelvis'].to_3x3().transposed())@rx(ang)@(M['B_Pelvis'].to_3x3()@R['B_Pelvis'].to_3x3().transposed()).transposed()@m.to_3x3(),m.translation)
   # Shoulders unwind past impact; neck/head counter-turn so the gaze keeps its target.
   twist=(.085*windup-.065*follow) if n.startswith('B_Spine') else (-.07*windup+.05*follow) if n=='B_Neck' else -.15*windup+.115*follow
   if twist:
    carry=M['B_Pelvis'].to_3x3()@R['B_Pelvis'].to_3x3().transposed()
    m=matrix(carry@Matrix.Rotation(twist,3,'Z')@carry.transposed()@m.to_3x3(),m.translation)
   if n=='B_Head' and fidget:m=matrix(Matrix.Rotation(.3*fidget,3,'Z')@m.to_3x3(),m.translation)
  M[n]=m
 # Arms reach targets expressed in the chest's carried rest frame.
 carrier=M['B_Spine2']@R['B_Spine2'].inverted();cr=carrier.to_3x3()
 for sd,sign in [('L',1),('R',-1)]:
  un,fn,hn=['B_'+sd+'_'+x for x in ['UpperArm','Forearm','Hand']];shoulder=M[un].translation;restW=Vector(B[hn]['head']);restE=Vector(B[fn]['head']);base=carrier@restW
  swing=.045*math.sin(cyc+(0 if sd=='L' else math.pi)) if gait else 0
  amount=cast*(1. if sd=='R' else .45);offset=Vector((sign*(.015+.04*gaze+.10*hit+.06*amount),-.035-swing-.12*gaze-.27*amount,.018+.025*gaze+.12*amount+.40*hit))
  if fall:offset=offset.lerp(Vector((sign*.14,-.16,.11)),fall)
  target=base+cr@offset;s=np.array(shoulder);v=np.array(target-shoulder);a=float(np.linalg.norm(restE-Vector(B[un]['head'])));b=float(np.linalg.norm(restW-restE));dist=np.clip(np.linalg.norm(v),abs(a-b)+.005,a+b-.003);axis=norm(v);target=s+axis*dist
  pole=np.array(carrier@restE+cr@Vector((sign*.09,.08,0)))-s;pole=norm(pole-axis*(pole@axis));along=(a*a-b*b+dist*dist)/(2*dist);elbow=s+axis*along+pole*math.sqrt(max(0,a*a-along*along))
  for n,start,end,restend in [(un,s,elbow,B[fn]['head']),(fn,elbow,target,B[hn]['head'])]:
   orig=cr@Vector(np.array(restend)-np.array(B[n]['head']));q=orig.rotation_difference(Vector(end-start));M[n]=matrix(q.to_matrix()@cr@R[n].to_3x3(),start)
  delta=M[fn].to_3x3()@R[fn].to_3x3().transposed();M[hn]=matrix(delta@R[hn].to_3x3(),target)
  for f in range(5):
   ns=[f'B_{sd}_Finger{f}'+x for x in ['','1','2']]
   for i,n in enumerate(ns):
    parent=B[n]['parent'];m=M[parent]@REL[n];curl=(.10 if f else .06)+.045*math.sin(cyc+f)*float(role=='Standing')+.07*gaze+.10*hit+.18*fall-.08*amount
    m=m@Matrix.Rotation(max(0,curl)*(1 if i<2 else .75),4,'X');M[n]=m
 # A small phase offset per strand keeps the crown alive; the gaze spreads and raises it.
 for k,snake in enumerate(D['snakes']):
  for i,n in enumerate(snake['names']):
   m=M[B[n]['parent']]@REL[n];phase=cyc+k*.8-i*.6;motion=(.05*math.sin(phase)+.08*gaze*math.sin(k+1)+.045*cast)*(1-fall)+.05*hit;M[n]=m@Matrix.Rotation(motion,4,'X')@Matrix.Rotation(.028*math.cos(phase)*(1-fall),4,'Z')
 for n in B:
  pb=rig.pose.bones[n];parent=B[n]['parent'];basis=REL[n].inverted()@(M[parent].inverted()@M[n] if parent else M[n]);pb.matrix_basis=basis
 bpy.context.view_layer.update()
 # Use the actual deformed surface for final ground contact, not only joint centres.
 deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps);mesh=evaluated.to_mesh();z=min(v.co.z for v in mesh.vertices);evaluated.to_mesh_clear()
 if z<0:rig.pose.bones['Root'].location+=R['Root'].to_3x3().transposed()@Vector((0,0,-z));bpy.context.view_layer.update()
 return {'fall':fall,'hit':hit,'gaze':gaze,'cast':cast}
rig.animation_data_clear();reports={}
for old in list(bpy.data.actions):bpy.data.actions.remove(old)
for role,duration in LOOPS.items():
 action=bpy.data.actions.new(role);action.use_fake_user=True;count=round(duration*FPS);keys={n:[] for n in B};worst={part:[] for part in ['body','arms','hands','head','crown']};mins=[];first=None;last=None
 for frame in range(count+1):
  rig.animation_data_clear();pose(role,frame/FPS);deps=bpy.context.evaluated_depsgraph_get();obj=body.evaluated_get(deps);mesh=obj.to_mesh();c=np.array([v.co[:] for v in mesh.vertices]);obj.to_mesh_clear();first=c.copy() if first is None else first;last=c;stretch=np.linalg.norm(c[E[:,1]]-c[E[:,0]],axis=1)/np.maximum(EL,1e-8);mins.append(float(c[:,2].min()))
  masks={'body':PART==0,'arms':np.isin(PART,[6,9]),'hands':np.isin(PART,[1,4]),'head':np.isin(PART,[101,104,106,121,123]),'crown':(PART>=100)&~np.isin(PART,[101,104,106,121,123])}
  for part,mask in masks.items():
   s=stretch[mask[E[:,0]]&mask[E[:,1]]&USE];worst[part].append([float(np.percentile(s,99)),float(s.max())])
  for n in B:
   pb=rig.pose.bones[n];keys[n].append((pb.location.copy(),pb.rotation_quaternion.copy()))
 rig.animation_data_create();rig.animation_data.action=action
 for frame in range(count+1):
  for n in B:
   pb=rig.pose.bones[n];pb.location,pb.rotation_quaternion=keys[n][frame];pb.keyframe_insert('location',frame=frame+1,group=n);pb.keyframe_insert('rotation_quaternion',frame=frame+1,group=n)
 for layer in action.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 reports[role]={'duration':count/FPS,'min_z':min(mins),'loop_delta':float(np.linalg.norm(last-first,axis=1).max()),'stretch':{p:np.max(a,axis=0).tolist() for p,a in worst.items()}};print(role,json.dumps(reports[role]))
for role,report in reports.items():
 assert report['min_z']>-.001,(role,report)
 assert report['stretch']['arms'][0]<2 and report['stretch']['hands'][1]<4.5 and report['stretch']['crown'][1]<2,(role,report)
 if role in ['Standing','Walk','Running','Dead']:assert report['loop_delta']<.001,(role,report['loop_delta'])
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'));(P/'work/animation_audit.json').write_text(json.dumps(reports,indent=2)+'\n')
