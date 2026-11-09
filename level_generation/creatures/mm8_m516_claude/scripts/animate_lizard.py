"""Native-paced biped clips with analytic hock IK, sole contacts and tail counterbalance."""
import bpy,sys,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_ckt_claude/scripts'));import posing as U
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;FPS=24;sc.render.fps=FPS
DATA=json.loads((P/'work/rig.json').read_text());NAMES=list(DATA['bones']);X,Y,Z=Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1));REST={s:{k:Vector(v) for k,v in zip(['hip','knee','hock','ankle','toe'],DATA['legs'][s])} for s in 'LR'}
Q={s:rig.pose.bones['Foot_'+s].matrix.to_quaternion().copy() for s in 'LR'};C=np.array([v.co[:] for v in body.data.vertices]);E=np.array([e.vertices[:] for e in body.data.edges]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1);VALID=EL>.002
FEET={s:np.where((C[:,0]*(1 if s=='L' else -1)>0)&(C[:,2]<.115))[0] for s in 'LR'}
DUR={'Standing':2.,'Walking':1.,'Running':.75,'Attack':1.25,'Hit':.625,'Death':1.,'Dead':.25,'Fidget':.625};STRIDE={'Walking':1.0,'Running':1.8}
def ss(x):
 x=min(1.,max(0.,x));return x*x*(3-2*x)
def rot(n,axis,d):U.rotate_world(rig,n,axis,d)
def co():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',a);ev.to_mesh_clear();return a.reshape(-1,3)
def offset(v):
 b=rig.pose.bones['Hips'];b.matrix=Matrix.Translation(Vector(v))@b.matrix;bpy.context.view_layer.update()
def torso(lift=0.,fwd=0.,side=0.,pitch=0.,roll=0.,yaw=0.):
 offset((side,-fwd,lift));rot('Hips',Z,yaw);rot('Hips',Y,roll);rot('Hips',X,pitch)
def head(pitch=0.,yaw=0.,jaw=0.,fan=0.):
 for n,w in [('Neck1',.28),('Neck2',.37),('Head',.35)]:rot(n,X,-pitch*w);rot(n,Z,yaw*w)
 rot('Jaw',X,jaw)
 for s,k in [('L',1),('R',-1)]:rot('Frill_'+s,Z,-k*fan)
def tail(t,period=2.,sway=2.,lift=0.,counter=0.):
 for i in range(8):
  rot('Tail'+str(i+1),Z,sway*(.45+i*.10)*math.sin(2*math.pi*t/period-i*.38)+counter/(i+1));rot('Tail'+str(i+1),X,lift*(1-i*.09))
def arms(t,period=2.,amount=2.,up=0.,axis=X):
 for s in 'LR':
  w=2*math.pi*t/period+(0 if s=='L' else math.pi);rot('UpperArm_'+s,axis,up+amount*math.sin(w));rot('ForeArm_'+s,axis,-amount*.7*math.sin(w-.4));rot('Hand_'+s,axis,amount*.4*math.sin(w-.8))
def leg(s,ankle,pitch=0.,toe=0.):
 r=REST[s];tv=Matrix.Rotation(math.radians(-pitch),3,X)@(r['ankle']-r['hock']);hock=Vector(ankle)-tv;hip=rig.pose.bones['Thigh_'+s].head.copy();pole=hip+Vector((0,-1,0))
 U.two_bone_ik(rig,'Thigh_'+s,'Shin_'+s,hock,pole);U.aim_bone(rig,'Tarsus_'+s,Vector(ankle));f=rig.pose.bones['Foot_'+s];f.matrix=Matrix.LocRotScale(f.head.copy(),Quaternion(X,math.radians(-toe))@Q[s],Vector((1,1,1)));bpy.context.view_layer.update()
 return (rig.pose.bones['Foot_'+s].head-Vector(ankle)).length
def planted(s,ankle,lift=0.,pitch=0.,toe=0.):
 target=Vector(ankle);target.z+=lift;leg(s,target,pitch,toe)
 dz=.008+lift-float(co()[FEET[s],2].min());target.z+=dz;error=leg(s,target,pitch,toe);return error,abs(float(co()[FEET[s],2].min())-(.008+lift)),target.copy()
def keys(rows,t):
 if t<=rows[0][0]:return rows[0][1].copy()
 for (a,x),(b,y) in zip(rows[:-1],rows[1:]):
  if t<=b:
   u=ss((t-a)/(b-a));return {k:x.get(k,0)*(1-u)+y.get(k,0)*u for k in set(x)|set(y)}
 return rows[-1][1].copy()
# ac rears over the right leg; ae/af sweep down across to the creature's right.
ATTACK=[
 (0,{}),
 (.18,{'lift':-.08,'pitch':10,'hp':-8,'up':-15}),
 (.50,{'lift':.12,'fwd':-.10,'side':-.10,'pitch':-34,'roll':10,'yaw':9,
        'hp':29,'hy':22,'jaw':29,'up':-36,'fan':15,'step':.36,'spread':28}),
 (.68,{'lift':.08,'fwd':-.04,'side':-.07,'pitch':-25,'roll':7,'yaw':7,
        'hp':20,'hy':15,'jaw':33,'up':-28,'fan':16,'step':.20,'spread':35}),
 (.88,{'lift':-.10,'fwd':.20,'side':-.035,'pitch':21,'roll':-6,'yaw':-7,
        'hp':-22,'hy':-16,'jaw':24,'up':8,'fan':13,'spread':42}),
 (1.,{'lift':-.16,'fwd':.24,'side':-.05,'pitch':29,'roll':-10,'yaw':-10,
       'hp':-30,'hy':-22,'jaw':2,'up':16,'fan':9,'spread':42}),
 (1.10,{'lift':-.13,'fwd':.18,'side':-.04,'pitch':22,'roll':-7,'yaw':-7,
        'hp':-21,'hy':-14,'jaw':3,'up':13,'fan':6,'spread':24}),
 (1.25,{})]
HIT=[(0,{}),(.12,{'pitch':-10,'hp':18,'hy':-20,'jaw':12,'roll':-8,'up':-16}),(.34,{'lift':-.05,'pitch':11,'hp':-18,'hy':12,'roll':8,'up':18}),(.625,{})]
FIDGET=[(0,{}),(.22,{'hp':7,'jaw':14,'fan':7,'up':-8}),(.39,{'hp':16,'jaw':22,'hy':9,'fan':13,'up':-14}),(.625,{})]
DEATH=[(0,{}),(.15,{'pitch':-9,'hp':18,'hy':-13,'jaw':10}),(.37,{'lift':.01,'pitch':-25,'hp':22,'jaw':25,'roll':12,'up':-25}),(.60,{'lift':-.12,'pitch':-16,'hp':10,'jaw':19,'roll':50,'up':-16}),(.84,{'lift':-.58,'pitch':12,'hp':-10,'jaw':9,'roll':92,'up':12}),(1.,{'lift':-.66,'pitch':9,'hp':-17,'jaw':5,'roll':89,'up':14})]
def pose(role,t):
 U.reset(rig);errors=[];contacts=[];feet={};fall=0.
 if role in STRIDE:
  dur=DUR[role];p=(t/dur)%1.;w=2*math.pi*p;run=role=='Running';duty=.45 if run else .62;stride=STRIDE[role];yaw=3*math.sin(w)
  torso(lift=(-.13+.05*math.cos(2*w)) if run else (-.095+.014*math.cos(2*w)),side=.105*math.sin(w),pitch=12 if run else 7,roll=-4*math.sin(w),yaw=yaw);head(pitch=8 if run else 5,yaw=-yaw,jaw=2+2*math.sin(2*w));tail(t,dur,3.5 if run else 2.4,lift=1.2 if run else .3,counter=-yaw*.7);arms(t,dur,9 if run else 5)
  for s in 'LR':
   phase=(p+(0 if s=='L' else .5))%1.;a=REST[s]['ankle'].copy();a.y=.16 if run else .27
   if phase<duty:a.y+=stride*(phase-duty/2);lift=toe=tp=0.
   else:
    u=(phase-duty)/(1-duty);a.y+=stride*duty*(.5-ss(u));lift=(.20 if run else .13)*math.sin(math.pi*u);toe=22*math.sin(math.pi*u);tp=12*math.sin(math.pi*u)
   err,contact,target=planted(s,a,lift,tp,toe);errors.append(err)
   if lift<1e-7:contacts.append(contact)
   feet[s]={'phase':phase,'stance':phase<duty,'ankle':list(rig.pose.bones['Foot_'+s].head),'target':list(target)}
 elif role=='Standing':
  w=2*math.pi*t/2;torso(lift=.004*math.sin(w),pitch=.7*math.sin(w));head(pitch=1.2*math.sin(w+.2),yaw=2.3*math.sin(w));tail(t,sway=2);arms(t,amount=1.5)
  for s in 'LR':
   e,c,_=planted(s,REST[s]['ankle']);errors.append(e);contacts.append(c)
 else:
  tt=1. if role=='Dead' else t;rows={'Attack':ATTACK,'Hit':HIT,'Fidget':FIDGET,'Death':DEATH,'Dead':DEATH}[role];k=keys(rows,tt);g=lambda n:k.get(n,0.);torso(lift=g('lift'),fwd=g('fwd'),side=g('side'),pitch=g('pitch'),roll=g('roll'),yaw=g('yaw'));head(g('hp'),g('hy'),g('jaw'),g('fan'));body_x=(rig.pose.bones['Hips'].matrix@rig.data.bones['Hips'].matrix_local.inverted()).to_3x3()@X;arms(tt,1.,0.,g('up'),body_x if role in ['Death','Dead'] else X);tail(0.,1.,0.,lift=-g('pitch')*.20,counter=-g('hy')*.12)
  if role=='Attack':
   body_y=(rig.pose.bones['Hips'].matrix@rig.data.bones['Hips'].matrix_local.inverted()).to_3x3()@Y
   for side,sign in [('L',1),('R',-1)]:rot('UpperArm_'+side,body_y,-sign*g('spread'))
  if role in ['Death','Dead']:fall=ss((tt-.38)/.44)
  for s,sg in [('L',1),('R',-1)]:
   if fall:
    rot('Thigh_'+s,body_x,50*fall);rot('Shin_'+s,body_x,-95*fall);rot('Tarsus_'+s,body_x,55*fall);rot('Foot_'+s,body_x,15*fall);f=rig.pose.bones['Foot_'+s];f.matrix=Matrix.LocRotScale(f.head.copy(),f.matrix.to_quaternion().slerp(Q[s],fall),Vector((1,1,1)));bpy.context.view_layer.update()
   else:
    a=REST[s]['ankle'].copy();lift=g('step') if role=='Attack' and s=='L' else 0.
    if lift:a.y-=lift*.45
    e,c,_=planted(s,a,lift,toe=lift*38);errors.append(e)
    if not lift:contacts.append(c)
  if fall:rot('Tail1',X,-13.5*fall);offset((0,0,.006-float(co()[:,2].min())))
 if not fall:
  for _ in range(12):
   if float(co()[C[:,1]>.78,2].min())>=.006:break
   rot('Tail1',X,1.)
 return {'ik_error':max(errors,default=0.),'contact_error':max(contacts,default=0.),'feet':feet}
reports={}
for old in list(bpy.data.actions):bpy.data.actions.remove(old)
for role,duration in DUR.items():
 frames=round(duration*FPS);samples={n:[] for n in NAMES};floors=[];errors=[];contacts=[];ratios=[];trajectory=[];first=None
 for f in range(frames+1):
  rig.animation_data_clear();m=pose(role,f/FPS);a=co();first=a.copy() if first is None else first;last=a;floors.append(float(a[:,2].min()));errors.append(m['ik_error']);contacts.append(m['contact_error']);trajectory.append(m['feet']);r=np.linalg.norm(a[E[:,1]]-a[E[:,0]],axis=1)/np.maximum(EL,1e-8);ratios.append([float(np.percentile(r[VALID],99)),float(r[VALID].max())])
  for n in NAMES:
   b=rig.pose.bones[n];q=b.rotation_quaternion.copy()
   if samples[n] and q.dot(samples[n][-1][1])<0:q.negate()
   samples[n].append((b.location.copy(),q))
 action=bpy.data.actions.new(role);action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action
 for f in range(frames+1):
  for n in NAMES:
   b=rig.pose.bones[n];b.location,b.rotation_quaternion=samples[n][f];b.keyframe_insert('location',frame=f+1,group=n);b.keyframe_insert('rotation_quaternion',frame=f+1,group=n)
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 reports[role]={'duration':duration,'min_z':min(floors),'max_ik_error':max(errors),'max_contact_error':max(contacts),'loop_delta':float(np.linalg.norm(last-first,axis=1).max()),'stretch_p99_max':np.max(ratios,axis=0).tolist(),'stride_length':STRIDE.get(role),'foot_trajectory':trajectory};print(role,{k:v for k,v in reports[role].items() if k!='foot_trajectory'},flush=True)
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'));(P/'work/animation_audit.json').write_text(json.dumps(reports,indent=2)+'\n')
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True;sc.display.shading.color_type='MATERIAL';sc.render.resolution_x=sc.render.resolution_y=700;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=3.8
for role,t in [('Standing',0),('Walking',.125),('Walking',.333),('Running',.25),('Attack',.5),('Attack',1.),('Hit',.125),('Fidget',.375),('Death',.375),('Death',.75),('Dead',0)]:
 rig.animation_data.action=bpy.data.actions[role];sc.frame_set(round(t*FPS)+1)
 for label,pos in [('side',(7,.55,1.3)),('quarter',(4,-6,2.8))]:
  target=Vector((0,.55,1.0));cam.location=pos;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/'review'/f'pilot_{role}_{int(t*100):02d}_{label}.png');bpy.ops.render.render(write_still=True)
