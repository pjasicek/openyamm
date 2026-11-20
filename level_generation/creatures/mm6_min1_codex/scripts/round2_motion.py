"""Keep accepted spatial swing; repair head curves, early timing, and a library-driven single fall."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_sources.blend'))
r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];axe=bpy.data.objects['AxeMesh'];sc=bpy.context.scene;sc.render.fps=240
names=list(r.pose.bones.keys());rest={n:b.matrix_local.copy() for n,b in r.data.bones.items()}
def update():bpy.context.view_layer.update()
def sample(a,f):
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(math.floor(f),subframe=f%1)
 return {n:p.matrix_basis.copy() for n,p in r.pose.bones.items()}
def apply(row):
 r.animation_data.action=None
 for n,m in row.items():r.pose.bones[n].matrix_basis=m
 update()
def snap():return {n:p.matrix_basis.copy() for n,p in r.pose.bones.items()}
def smooth(t):t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))
def mix(a,b,t):return {n:Matrix.LocRotScale(a[n].translation.lerp(b[n].translation,t),a[n].to_quaternion().slerp(b[n].to_quaternion(),t),Vector((1,1,1))) for n in names}
def points(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();v=np.array([x.co[:] for x in me.vertices]);e.to_mesh_clear();return v
def write(role,rows):
 r.animation_data.action=None
 if role in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions[role])
 a=bpy.data.actions.new(role);a.use_fake_user=True;prev={}
 for i,row in enumerate(rows):
  apply(row);r.animation_data.action=a
  for n in names:
   pb=r.pose.bones[n];q=pb.matrix_basis.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q.negate()
   prev[n]=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=i);pb.keyframe_insert('location',frame=i)
  r.animation_data.action=None
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 return a

def basis(x,y):
 x=x.normalized();y=(y-x*y.dot(x)).normalized();return Matrix((x,y,x.cross(y))).transposed()
def twist(q,axis):return (2*math.atan2(Vector(q[1:]).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi
def repair_arms(t):
 if t<=.18:return
 w=smooth((t-.18)/.30)
 for s,sign in [('R',-1),('L',1)]:
  un,fn,hn=[f'B_{s}_{k}' for k in ['UpperArm','Forearm','Hand']]
  U,E,H=[r.pose.bones[n].matrix.translation.copy() for n in [un,fn,hn]];HR=r.pose.bones[hn].matrix.to_3x3()
  ru=(rest[fn].translation-rest[un].translation).normalized();rf=(rest[hn].translation-rest[fn].translation).normalized();la=(rest[fn].translation-rest[un].translation).length;lb=(rest[hn].translation-rest[fn].translation).length
  H+=Vector((sign*.20,-.25,.20*smooth((1.0-t)/.4)))*w
  d=(H-U).normalized();dist=min((H-U).length,(la+lb)*.99);H=U+d*dist;cc=max(-1,min(1,(la*la+dist*dist-lb*lb)/(2*la*dist)));center=U+d*la*cc;chest=r.pose.bones['B_Spine2'].matrix.to_3x3();local_d=chest.inverted()@d;pole=chest@(initial_directions[s].rotation_difference(local_d)@initial_poles[s]);pole=(pole-d*pole.dot(d)).normalized();E=center+pole*la*math.sqrt(1-cc*cc)
  up=(E-U).normalized();fo=(H-E).normalized();rb=basis(ru,Vector((0,-1,0)));UD=basis(up,fo-up*fo.dot(up))@rb.transposed();UR=UD@rest[un].to_3x3();FR=(UD@rf).rotation_difference(fo).to_matrix()@UD@rest[fn].to_3x3()
  # The library's wrist roll is excessive on the bull's much broader hands; soften it after release.
  neutral=FR@rest[fn].to_3x3().inverted()@rest[hn].to_3x3()
  relative=(neutral.inverted()@HR).to_quaternion();axis=(rest[hn].to_3x3().inverted()@rf).normalized();roll=twist(relative,axis);sw=relative@Quaternion(axis,-roll)
  clamped=Quaternion().slerp(sw,min(1,math.radians(40)/max(sw.angle,1e-8)))@Quaternion(axis,max(-math.radians(30),min(math.radians(30),roll)))
  HR=neutral@relative.slerp(clamped,w).to_matrix()
  for n,rot,pos in [(un,UR,U),(fn,FR,E),(hn,HR,H)]:
   desired=Matrix.LocRotScale(pos,rot.to_quaternion(),Vector((1,1,1)))
   # Ease out of the fixed initial grasp without a discontinuity at release.
   r.pose.bones[n].matrix=desired;update()
  ua=(rest[un].inverted()@rest[fn].translation).normalized();ut=twist(r.pose.bones[un].rotation_quaternion,ua);r.pose.bones[f'B_{s}_UpperArmTwist'].rotation_quaternion=Quaternion(ua,-.5*ut);update();axisf=(rest[fn].inverted()@rest[hn].translation).normalized();r.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion=stand[f'B_{s}_ForearmTwist'].to_quaternion().slerp(Quaternion(axisf,.6*max(-math.radians(60),min(math.radians(60),roll))),w);update()

stand=sample(bpy.data.actions['Standing'],0);apply(stand);AR=r.pose.bones['B_R_Hand'].matrix.inverted()@r.pose.bones['Axe'].matrix
initial_poles={};initial_directions={}
for side in 'RL':
 U,E,H=[r.pose.bones[f'B_{side}_{n}'].matrix.translation.copy() for n in ['UpperArm','Forearm','Hand']];direction=(H-U).normalized();pole=(E-U)-direction*(E-U).dot(direction);initial_poles[side]=r.pose.bones['B_Spine2'].matrix.to_3x3().inverted()@pole.normalized();initial_directions[side]=r.pose.bones['B_Spine2'].matrix.to_3x3().inverted()@direction
report={'attack':{},'death':{'source':'anim_library/mixamo/Two Handed Sword Death.fbx','release_s':.18,'duration_s':2.4},'horns':'Existing rigid B_Head weights retained; no geometry changes.'}
for role in ['Attack','Cast']:
 a=bpy.data.actions[role];dur=a.frame_range[1]/240;rows=[sample(a,float(f)) for f in range(math.ceil(dur*240)+1)]
 for n in ['B_Neck','B_Head']:
  qs=np.array([list(row[n].to_quaternion()) for row in rows])
  for i in range(1,len(qs)):
   if qs[i]@qs[i-1]<0:qs[i]*=-1
  sigma=13.;rad=39;weights=np.exp(-np.arange(-rad,rad+1)**2/(2*sigma*sigma));weights/=weights.sum();qs2=np.stack([np.convolve(np.pad(qs[:,j],rad,mode='edge'),weights,mode='valid') for j in range(4)],axis=1)
  for i,row in enumerate(rows):
   q=Quaternion(qs2[i]);q.normalize();row[n]=Matrix.LocRotScale(row[n].translation,q,Vector((1,1,1)))
 if role=='Attack':
  # 25% faster early wind-up, smooth return to original rate before the release.
  ts=np.arange(len(rows))/240;rate=.8+.2*np.array([smooth((t-.45)/.4) for t in ts]);tt=np.r_[0,np.cumsum((rate[:-1]+rate[1:])*.5/240)];newdur=math.floor(tt[-1]*240)/240
  assert np.all(np.diff(tt)>0), "The attack time map must be strictly increasing"
  out=[]
  for t in np.arange(round(newdur*240)+1)/240:
   sf=float(np.interp(t,tt,ts))*240;i=min(int(sf),len(rows)-2);out.append(mix(rows[i],rows[i+1],sf-i))
  report['attack']={'duration_s':newdur,'old_impact_s':1.075,'impact_s':float(np.interp(1.075,ts,tt)),'early_rate':.8};rows=out
 write(role,rows)
source=bpy.data.actions['SwordDeath'];rows=[];release=None
source_rows=[sample(source,i/8) for i in range(577)]
for n in names:
 if any(k in n for k in ['UpperArm','Forearm','Hand','Neck','Head']):
  qs=np.array([list(row[n].to_quaternion()) for row in source_rows])
  for j in range(1,len(qs)):
   if qs[j]@qs[j-1]<0:qs[j]*=-1
  weights=np.exp(-np.arange(-24,25)**2/(2*8.0**2));weights/=weights.sum();filtered=np.stack([np.convolve(np.pad(qs[:,j],24,mode='edge'),weights,mode='valid') for j in range(4)],axis=1)
  for j,row in enumerate(source_rows):q=Quaternion(filtered[j]);q.normalize();row[n]=Matrix.LocRotScale(row[n].translation,q,Vector((1,1,1)))
# Source motion is kept at its original 30 Hz timing; the floor is fitted to the entire bull silhouette.
for i in range(577):
 t=i/240;row=source_rows[i];row=mix(stand,row,smooth(t/.35))
 # Delay arm opening until the shaft is released, with a continuous transition to the library's reaching arms.
 for n in names:
  if any(k in n for k in ['Clavicle','UpperArm','Forearm','Hand','Finger']):row[n]=mix(stand,row,smooth((t-.18)/.4))[n]
 apply(row)
 repair_arms(t)
 for side in 'RL':
  for n in names:
   if n.startswith(f'B_{side}_Finger'):
    amount=.45 if 'Finger0' in n else .72;begin=.02 if side=='L' else .08; q=stand[n].to_quaternion().slerp(Quaternion(),amount*smooth((t-begin)/.22));r.pose.bones[n].rotation_quaternion=q
 update()
 low=float(points(body)[:,2].min());m=r.pose.bones['B_Pelvis'].matrix.copy();m.translation.z+=.001-low;r.pose.bones['B_Pelvis'].matrix=m;update()
 if t<=.18+1e-8:
  r.pose.bones['Axe'].matrix=r.pose.bones['B_R_Hand'].matrix@AR;update();release=r.pose.bones['Axe'].matrix.copy();releasepts=points(axe);lowrel=float(releasepts[:,2].min())
 else:
  dt=t-.18;m=release.copy();drop=-.35*dt-4.905*dt*dt;hit=(-.35+math.sqrt(.35*.35+19.62*max(0,lowrel-.001)))/9.81
  # Free flight has downward initial velocity. Once down, settle around the contact patch.
  flight=min(dt,hit);m.translation+=Vector((-1.2*flight,-1.0*flight,-.35*flight-4.905*flight*flight))
  if dt>hit:
   q=(release@rest['Axe'].inverted()).to_quaternion();normal=q@Vector((0,1,0));delta=normal.rotation_difference(Vector((0,0,1)));v=smooth((dt-hit)/.35);rot=Quaternion().slerp(delta,v).to_matrix();loc=m.translation.copy();m=rot.to_4x4()@m;m.translation=loc
  r.pose.bones['Axe'].matrix=m;update();lo=float(points(axe)[:,2].min())
  if lo<.001 or dt>hit:m=r.pose.bones['Axe'].matrix.copy();m.translation.z+=.001-lo;r.pose.bones['Axe'].matrix=m;update()
 rows.append(snap())
# Smooth released wrists in their local frames, preserving the exact held interval.
for n in ['B_L_Hand','B_R_Hand']:
 qs=np.array([list(row[n].to_quaternion()) for row in rows])
 for j in range(1,len(qs)):
  if qs[j]@qs[j-1]<0:qs[j]*=-1
 weights=np.exp(-np.arange(-48,49)**2/(2*16.0**2));weights/=weights.sum();filtered=np.stack([np.convolve(np.pad(qs[:,j],48,mode='edge'),weights,mode='valid') for j in range(4)],axis=1)
 for j,row in enumerate(rows):
  q=Quaternion(filtered[j]);q.normalize();q=row[n].to_quaternion().slerp(q,smooth((j/240-.18)/.25));row[n]=Matrix.LocRotScale(row[n].translation,q,Vector((1,1,1)))
for j,row in enumerate(rows):
 apply(row);saved_axe=r.pose.bones['Axe'].matrix.copy();m=r.pose.bones['B_Pelvis'].matrix.copy();m.translation.z+=.001-float(points(body)[:,2].min());r.pose.bones['B_Pelvis'].matrix=m;update();r.pose.bones['Axe'].matrix=saved_axe;update();rows[j]=snap()
write('Death',rows);write('Dead',[rows[-1]]*241)
for a in list(bpy.data.actions):
 if a.name not in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:bpy.data.actions.remove(a)
apply(stand);r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2_candidate.blend'))
(P/'review/round2/motion_changes.json').write_text(json.dumps(report,indent=2))
print('ROUND2',report,flush=True)
