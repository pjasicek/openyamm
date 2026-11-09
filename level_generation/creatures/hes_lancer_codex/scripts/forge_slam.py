"""Keep the accepted RPG windup, author a grounded hammer arc, fit anatomical two-hand IK globally."""
import bpy,sys,os,json,math
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_strike_20261024/work/forge_complete.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;old=bpy.data.actions['Forge_Attack']
G={s:json.loads((P/f'work/grip_pose_{"R" if s=="R" else "L_tun"}.json').read_text()) for s in 'LR'};C={s:Vector(G[s]['handle_centre_hand_local']) for s in 'LR'}
def sample(f):
 r.animation_data.action=old;r.animation_data.action_slot=old.slots[0];sc.frame_set(int(f),subframe=float(f%1));return {b.name:b.matrix_basis.copy() for b in r.pose.bones}
def apply(pose):
 r.animation_data.action=None
 for n,m in pose.items():r.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def smooth(u):
 u=max(0.,min(1.,u));return u*u*(3-2*u)
def leg(side,target):
 th,ca,ft=[f'B_{side}_{n}' for n in ('Thigh','Calf','Foot')];H,K,A=[armik.W(r,n).translation.copy() for n in (th,ca,ft)];d=target.translation-H;l1,l2=(K-H).length,(A-K).length;u=d.normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();co=(l1*l1+d.length_squared-l2*l2)/(2*l1*d.length);assert abs(co)<1;Kn=H+l1*(u*co+v*math.sqrt(1-co*co))
 for name,child,goal in ((th,ca,Kn),(ca,ft,target.translation)):
  m=armik.W(r,name);cur=armik.W(r,child).translation-m.translation;rot=cur.normalized().rotation_difference((goal-m.translation).normalized());armik.set_world(r,name,armik.rot_world(m,rot.to_matrix()@m.to_3x3()))
 armik.set_world(r,ft,armik.rot_world(armik.W(r,ft),target.to_3x3()))
sample(36);qstart={s:np.array([armik.W(r,f'B_{s}_{n}').to_quaternion()[:] for n in ('UpperArm','Forearm','Hand')]) for s in 'LR'};wm=armik.W(r,'Thunder_Maul');wq=wm.to_quaternion();h0=wm@Vector((0,1.02,0));axis0=wm.to_3x3()@Vector((0,1,0));localH={s:wm.to_3x3().inverted()@armik.W(r,f'B_{s}_Hand').to_3x3() for s in 'LR'};grip0={s:(wm.inverted()@(armik.W(r,f'B_{s}_Hand')@C[s])).y for s in 'LR'}
sample(75);qend={s:np.array([armik.W(r,f'B_{s}_{n}').to_quaternion()[:] for n in ('UpperArm','Forearm','Hand')]) for s in 'LR'};we=armik.W(r,'Thunder_Maul');he=we@Vector((0,1.02,0));qe=we.to_quaternion();localHE={s:we.to_3x3().inverted()@armik.W(r,f'B_{s}_Hand').to_3x3() for s in 'LR'};gripend={s:(we.inverted()@(armik.W(r,f'B_{s}_Hand')@C[s])).y for s in 'LR'}
impact=1.75;peak=1.2+.12*(impact-1.2)/.35;duration=3.5;end=105;headhit=Vector((0,-1.80,.38));axishit=Vector((.04,-.78,-.624)).normalized();qhit=axis0.rotation_difference(axishit)@wq
qpeak=axis0.rotation_difference(Vector((.16,-.12,.98)).normalized())@wq
rows=[];tables={s:[] for s in 'LR'};rest={s:(r.data.bones[f'B_{s}_Forearm'].matrix_local.to_3x3().inverted()@r.data.bones[f'B_{s}_Hand'].matrix_local.to_3x3()).inverted() for s in 'LR'};wa={s:(r.data.bones[f'B_{s}_Hand'].matrix_local.to_3x3().inverted()@(r.data.bones[f'B_{s}_Hand'].head_local-r.data.bones[f'B_{s}_Forearm'].head_local)).normalized() for s in 'LR'}
for f in np.arange(0,end+.001,.5):
 t=float(f/30)
 if t<=1.2:rows.append((float(f),sample(float(f)),None));continue
 recovery=smooth((t-2.0)/(duration-2.0));sf=36+(48-36)*smooth((t-1.2)/(impact-1.2)) if t<=2.0 else 48+(75-48)*recovery;pose=sample(sf);apronR={n:armik.W(r,n).to_3x3().copy() for n in ('B_ForgeApron_Front_1','B_ForgeApron_Front_2','B_ForgeApron_Back_1','B_ForgeApron_Back_2')};feet={s:armik.W(r,f'B_{s}_Foot').copy() for s in 'LR'};apply(pose)
 weight=smooth((t-1.2)/(impact-1.2))*(1-recovery);pel=armik.W(r,'B_Pelvis');pel.translation+=Vector((0,-.08,-.07))*weight;armik.set_world(r,'B_Pelvis',pel)
 for n,share in (('B_Spine',.50),('B_Spine1',.30),('B_Spine2',.20)):
  m=armik.W(r,n);armik.set_world(r,n,armik.rot_world(m,Quaternion((1,0,0),math.radians(32)*share*weight).to_matrix()@m.to_3x3()))
 for n,degrees in (('Bone_020',14),('B_Neck',-12)):
  m=armik.W(r,n);armik.set_world(r,n,armik.rot_world(m,Quaternion((1,0,0),math.radians(degrees)*weight).to_matrix()@m.to_3x3()))
 for s in 'LR':leg(s,feet[s])
 for n,R in apronR.items():
  m=armik.W(r,n);q=m.to_quaternion().slerp(R.to_quaternion(),weight);armik.set_world(r,n,armik.rot_world(m,q.to_matrix()))
 if t<=peak:
  u=smooth((t-1.2)/(peak-1.2));q=wq.slerp(qpeak,u);head=h0.lerp(Vector((.1,-.90,2.20)),u)
 elif t<=impact:
  u=smooth((t-peak)/(impact-peak));q=qpeak.slerp(qhit,u);head=Vector((.1,-.90,2.20)).lerp(headhit,u)
 elif t<=2.0:q=qhit;head=headhit+Vector((0,0,.002*smooth((t-impact)/.25)))
 else:
  q=qhit.slerp(qe,recovery);head=(headhit+Vector((0,0,.002))).lerp(he,recovery)
 head.x-=.25*smooth((t-1.55)/.18)*(1-recovery)**2
 axis=q@Vector((0,1,0));weapon=q.to_matrix().to_4x4();weapon.translation=head-axis*1.02;gripweight=smooth((t-1.2)/(impact-1.2))
 pose={b.name:b.matrix_basis.copy() for b in r.pose.bones}
 for s in 'LR':
  grip=(grip0[s]+((- .47 if s=='R' else -.17)-grip0[s])*gripweight)*(1-recovery)+gripend[s]*recovery;centre=weapon@Vector((0,grip,0));u,ff,h=[armik.W(r,f'B_{s}_{n}').copy() for n in ('UpperArm','Forearm','Hand')];sh,el,wr=u.translation,ff.translation,h.translation;l1,l2=(el-sh).length,(wr-el).length;choices=[];minsw=180;minreach=999
  for slide in ((0,-.04,.04) if s=='R' else (0,-.08,.08,-.16,.16,-.24,.24)):
   if not -.50<=grip+slide<=.65:continue
   if s=='L' and grip+slide<-.21:continue
   centre=weapon@Vector((0,grip+slide,0))
   for roll in range(-180,181,15):
    R=Quaternion(axis,math.radians(roll)).to_matrix()@q.to_matrix()@localH[s].to_quaternion().slerp(localHE[s].to_quaternion(),recovery).to_matrix();target=centre-R@C[s];d=target-sh;dist=d.length;minreach=min(minreach,dist/(l1+l2))
    if dist>.995*(l1+l2) or dist<abs(l1-l2)+.01:continue
    direction=d.normalized();normal=el-sh-direction*(el-sh).dot(direction);normal=normal.normalized() if normal.length>1e-6 else direction.orthogonal().normalized();ca=(l1*l1+dist*dist-l2*l2)/(2*l1*dist)
    for phi in range(-180,180,10):
     E=sh+l1*(direction*ca+(Quaternion(direction,math.radians(phi))@normal)*math.sqrt(1-ca*ca));rot=(el-sh).normalized().rotation_difference((E-sh).normalized());n0=rot@((el-sh).cross(wr-el));n1=(E-sh).cross(target-E);n0=(n0-direction*n0.dot(direction)).normalized() if n0.length<1e-8 else n0.normalized();n1.normalize();ax=(E-sh).normalized();n0=(n0-ax*n0.dot(ax)).normalized();n1=(n1-ax*n1.dot(ax)).normalized();rot=Quaternion(ax,math.atan2(ax.dot(n0.cross(n1)),n0.dot(n1)))@rot;ru=rot.to_matrix()@u.to_3x3();rf=(rot@(wr-el)).normalized().rotation_difference((target-E).normalized()).to_matrix()@rot.to_matrix()@ff.to_3x3();sw,tw=armik.split_swing_twist((rest[s]@(rf.inverted()@R)).to_quaternion(),wa[s]);swing=math.degrees(min(sw.angle,2*math.pi-sw.angle));twist=math.degrees(tw)
     minsw=min(minsw,swing)
     if swing>59.5 or abs(twist)>175:continue
     mats=[]
     for rot3,point in ((ru,sh),(rf,E),(R,target)):
      m=rot3.to_4x4();m.translation=point;mats.append(m)
     edgeweight=1-smooth((t-1.2)/.12)+smooth((t-(duration-.35))/.35);ref=np.array([m.to_quaternion()[:] for m in (u,ff,h)]);qs=np.array([m.to_quaternion()[:] for m in mats]);anchor=.4*edgeweight*np.sum(np.degrees(2*np.arccos(np.clip(np.abs(np.sum(qs*ref,axis=1)),0,1)))**2)
     cost=float(anchor)+100*slide*slide+.02*swing*swing+.12*abs(twist)+.005*phi*phi+.001*roll*roll;choices.append({'cost':cost,'mats':mats,'q':np.array([m.to_quaternion()[:] for m in mats]),'swing':swing,'twist':twist,'reach':dist/(l1+l2),'grip':grip+slide})
  assert choices,('NO_ARM',f,s,list(centre),list(sh),list(axis),minsw,minreach);choices=sorted(choices,key=lambda x:x['cost'])[:80];tables[s].append(choices)
 rows.append((float(f),pose,weapon))
 if int(f*2)%20==0:print('SLAM_CANDIDATES',f,len(tables['R'][-1]),flush=True)
paths={}
for s,frames in tables.items():
 costs=np.array([c['cost'] for c in frames[0]])+2*np.sum(np.degrees(2*np.arccos(np.clip(np.abs(np.sum(np.array([c['q'] for c in frames[0]])*qstart[s],axis=2)),0,1)))**2,axis=1);backs=[]
 for a,b in zip(frames,frames[1:]):
  angles=np.degrees(2*np.arccos(np.clip(np.abs(np.einsum('ajk,bjk->abj',np.array([c['q'] for c in a]),np.array([c['q'] for c in b]))),0,1)));transition=.20*np.sum(angles**2,axis=2);table=costs[:,None]+transition;back=table.argmin(0);costs=table[back,np.arange(len(b))]+np.array([c['cost'] for c in b]);backs.append(back)
 costs+=2*np.sum(np.degrees(2*np.arccos(np.clip(np.abs(np.sum(np.array([c['q'] for c in frames[-1]])*qend[s],axis=2)),0,1)))**2,axis=1)
 ix=int(costs.argmin());path=[ix]
 for b in reversed(backs):ix=int(b[ix]);path.append(ix)
 paths[s]=list(reversed(path))
# Bake helpers with unwrapped half twists; weapon world transform is independent of their skin correction.
result=[];j=0;twists={s:[] for s in 'LR'};report=[]
for f,pose,weapon in rows:
 apply(pose)
 if weapon is not None:
  rec={'frame':f};shoulders={s:armik.W(r,f'B_ForgeShoulder_{s}').copy() for s in 'LR'}
  for s in 'LR':
   c=tables[s][j][paths[s][j]]
   for n,m in zip(('UpperArm','Forearm','Hand'),c['mats']):armik.set_world(r,f'B_{s}_{n}',m)
   rec[s]={k:c[k] for k in ('swing','twist','reach','grip')}
  for s,m in shoulders.items():armik.set_world(r,f'B_ForgeShoulder_{s}',m)
  armik.set_world(r,'Thunder_Maul',weapon);report.append(rec);j+=1
 for s in 'LR':
  fore,hand,upper=[r.data.bones[f'B_{s}_{n}'] for n in ('Forearm','Hand','UpperArm')];ax=(upper.matrix_local.inverted()@fore.head_local).normalized();bx=(fore.matrix_local.inverted()@hand.head_local).normalized();_,ut=armik.split_swing_twist(r.pose.bones[upper.name].matrix_basis.to_quaternion(),ax);rel=(r.pose.bones[fore.name].matrix.inverted()@r.pose.bones[hand.name].matrix).to_quaternion();rr=(fore.matrix_local.inverted()@hand.matrix_local).to_quaternion();_,ft=armik.split_swing_twist(rel@rr.inverted(),bx);twists[s].append((ut,ft,ax,bx))
 result.append((f,{b.name:b.matrix_basis.copy() for b in r.pose.bones}))
for s,values in twists.items():
 angles=np.unwrap(np.array([[x[0],x[1]] for x in values]),axis=0)
 # Anchor to the already accepted windup helper at the splice, then follow continuous changes.
 anchor=72
 for k,n in enumerate(('UpperArmTwist','ForearmTwist')):
  bn=f'B_{s}_{n}';base=result[anchor][1][bn].to_quaternion();axis=values[anchor][k+2];factor=-.5 if k==0 else .5
  for i in range(anchor+1,len(result)):result[i][1][bn]=(Quaternion(axis,float(factor*(angles[i,k]-angles[anchor,k])))@base).to_matrix().to_4x4()
r.animation_data.action=None;bpy.data.actions.remove(old);a=bpy.data.actions.new('Forge_Attack');a.use_fake_user=True;r.animation_data.action=a;previous={}
for f,pose in result:
 for n,m in pose.items():
  b=r.pose.bones[n];q=m.to_quaternion()
  if n in previous and q.dot(previous[n])<0:q=-q
  previous[n]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
a.use_frame_range=True;a.frame_start=0;a.frame_end=end
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_slam.blend'));(P/'review/forge_slam_fit.json').write_text(json.dumps({'impact_s':impact,'duration_s':duration,'frames':report},indent=2)+'\n');sys.stdout.flush();os._exit(0)
