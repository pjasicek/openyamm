"""Source-driven heavy swing, fixed two-hand grip frames and full sole-plane IK."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_weighted_sources.blend'));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
RATE=30;sc.render.fps=30;names=list(r.pose.bones.keys());G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'RL'}
roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
def update():bpy.context.view_layer.update()
def M(n):return r.pose.bones[n].matrix.copy()
def snapshot():return {n:r.pose.bones[n].matrix_basis.copy() for n in names}
def apply(row):
 r.animation_data.action=None
 for n,m in row.items():r.pose.bones[n].matrix_basis=m
 update()
def setmat(n,m):r.pose.bones[n].matrix=m;r.pose.bones[n].scale=(1,1,1);update()
def transform(rot,loc):return Matrix.LocRotScale(loc,rot.to_quaternion(),Vector((1,1,1)))
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def sample(a,f):
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(f),subframe=f%1);return snapshot()
def mix(a,b,u):return {n:transform(a[n].to_quaternion().slerp(b[n].to_quaternion(),u).to_matrix(),a[n].translation.lerp(b[n].translation,u)) for n in names}
def coords():
 e=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();v=np.array([p.co[:] for p in me.vertices]);e.to_mesh_clear();return v
rest=np.array([v.co[:] for v in body.data.vertices]);sole={s:np.where((rest[:,2]<.025)&(rest[:,0]*sign>0))[0] for s,sign in [('R',-1),('L',1)]}
assert all(len(v)>20 for v in sole.values())
raw={nm:[sample(bpy.data.actions[nm],f) for f in np.linspace(0,bpy.data.actions[nm].frame_range[1],round(bpy.data.actions[nm].frame_range[1]/30*RATE)+1)] for nm in roles}
SOURCE='DownSlash';N=38
source={mode:[sample(bpy.data.actions[SOURCE+mode],f) for f in np.linspace(0,N,round(N/30*RATE)+1)] for mode in ['plant','turn']}
apply(raw['Standing'][0]);home={s:M(f'B_{s}_Foot') for s in 'RL'};basepel=M('B_Pelvis');axerest=r.data.bones['Axe'].matrix_local.copy();AR=M('B_R_Hand').inverted()@M('Axe')@axerest.inverted();A0=M('Axe')@axerest.inverted();Hframe={s:A0.to_3x3().inverted()@M(f'B_{s}_Hand').to_3x3() for s in 'RL'};gripz={s:(A0.inverted()@(M(f'B_{s}_Hand')@Vector(G[s]['handle_centre_hand_local']))).z for s in 'RL'}
gripz['L']=.35
restb={n:b.matrix_local.copy() for n,b in r.data.bones.items()}
def basis(x,y):x=x.normalized();y=(y-x*y.dot(x)).normalized();return Matrix((x,y,x.cross(y))).transposed()
def twist(q,axis):return (2*math.atan2(Vector(q[1:]).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi
armdata={}
for s in 'RL':
 un,fn,hn=[f'B_{s}_{v}' for v in ['UpperArm','Forearm','Hand']];U,F,H=[restb[n].translation for n in [un,fn,hn]];ru=(F-U).normalized();rf=(H-F).normalized();bend=Vector((0,-1,0));bend=(bend-ru*ru.dot(bend)).normalized();axis=(restb[fn].inverted()@H).normalized();armdata[s]=(un,fn,hn,(F-U).length,(H-F).length,ru,rf,basis(ru,bend),axis)
def arm(s,target,hrot,preferred=None):
 un,fn,hn,la,lb,ru,rf,rb,axis=armdata[s];sh=M(un).translation;v=target-sh;dist=min(v.length,(la+lb)*.998);d=v.normalized();co=max(-1,min(1,(la*la+dist*dist-lb*lb)/(2*la*dist)));rad=la*math.sqrt(max(0,1-co*co));center=sh+d*la*co
 pref=(M(fn).translation-sh) if preferred is None else preferred-sh;pol=(pref-d*pref.dot(d)).normalized()
 if pol.length<.1:pol=(Vector((0,0,-1))-d*d.z*-1).normalized()
 par=r.data.bones[un].parent.name;parentbase=M(par)@restb[par].inverted()@restb[un];uaxis=(restb[un].inverted()@restb[fn].translation).normalized();best=None
 torso=M('B_Pelvis').translation+Vector((0,-.035,.30));head=M('B_Head').translation+Vector((0,-.02,.025))
 for ai in range(118):
  if ai==97:refine=best_angle
  angle=-math.pi+ai*math.pi/48 if ai<97 else refine+(ai-107)*math.pi/480
  elbow=center+Quaternion(d,float(angle))@pol*rad;up=(elbow-sh).normalized();fo=(target-elbow).normalized();bend=(fo-up*fo.dot(up)).normalized();UD=basis(up,bend)@rb.transposed();UR=UD@restb[un].to_3x3();f0=UD@rf;FR=f0.rotation_difference(fo).to_matrix()@UD@restb[fn].to_3x3()
  q=(FR.inverted()@hrot@(restb[fn].to_3x3().inverted()@restb[hn].to_3x3()).inverted()).to_quaternion();roll=twist(q,axis);swing=(q@Quaternion(axis,-roll)).angle;upper=twist((parentbase.to_3x3().inverted()@UR).to_quaternion(),uaxis)
  score=2*swing*swing+.35*roll*roll+.08*upper*upper+40*max(0,abs(roll)-math.radians(85))**2+20*max(0,swing-math.radians(45))**2+2*max(0,abs(upper)-math.radians(65))**2+12*(elbow-(sh+pref)).length_squared
  for point in [elbow,elbow.lerp(target,.35),elbow.lerp(target,.70),target]:
   for cen,rad3 in [(torso,Vector((.36,.31,.40))),(torso-Vector((0,0,.20)),Vector((.31,.29,.25))),(head,Vector((.32,.34,.32)))]:
    d3=point-cen;inside=1-sum((d3[k]/rad3[k])**2 for k in range(3));score+=15*max(0,inside)**2
  if s=='L':
   other=[M('B_R_'+n).translation for n in ['UpperArm','Forearm','Hand']]
   for p in [elbow,elbow.lerp(target,.25),elbow.lerp(target,.5),elbow.lerp(target,.75)]:
    for aa,bb,rr in [(other[0],other[1],.17),(other[1],other[2],.15)]:
     dd=bb-aa;tt=max(0,min(1,(p-aa).dot(dd)/dd.length_squared));distance=(p-aa-dd*tt).length;score+=10000*max(0,rr-distance)**2
  if best is None or score<best[0]:best=(score,UR,FR,elbow,roll,swing,upper);best_angle=angle
 return best,sh

def solvearm(s,target,rot,preferred=None):
 v,sh=arm(s,target,rot,preferred);_,UR,FR,elbow,roll,swing,upper=v;un,fn,hn,*_=armdata[s];setmat(un,transform(UR,sh));setmat(fn,transform(FR,elbow));setmat(hn,transform(rot,target))
 axis=armdata[s][-1];r.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.6*roll)
 ua=(restb[un].inverted()@restb[fn].translation).normalized();r.pose.bones[f'B_{s}_UpperArmTwist'].rotation_quaternion=Quaternion(ua,-.5*upper);update();return [math.degrees(roll),math.degrees(swing),math.degrees(upper)]
def aim(n,c,d):
 m=M(n);q=(M(c).translation-m.translation).normalized().rotation_difference(d.normalized());setmat(n,transform(q.to_matrix()@m.to_3x3(),m.translation))
def leg(s,target,rot):
 un,fn,hn=[f'B_{s}_{v}' for v in ['Thigh','Calf','Foot']];U,F,H=[M(n).translation for n in [un,fn,hn]];la=(F-U).length;lb=(H-F).length;d=(target-U).normalized();dist=min((target-U).length,(la+lb)*.999);pole=Vector((0,-1,0));pole=(pole-d*pole.dot(d)).normalized();co=max(-1,min(1,(la*la+dist*dist-lb*lb)/(2*la*dist)));elbow=U+la*(d*co+pole*math.sqrt(1-co*co));aim(un,fn,elbow-U);aim(fn,hn,target-M(fn).translation);setmat(hn,transform(rot,M(hn).translation))
def flatten(s,z=0):
 for it in range(3):
  pts=coords()[sole[s]];n=np.linalg.svd(pts-pts.mean(0))[2][-1];n=n if n[2]>0 else -n;delta=Vector(n).rotation_difference(Vector((0,0,1))).to_matrix();foot=M(f'B_{s}_Foot');leg(s,foot.translation,delta@foot.to_3x3());pts=coords()[sole[s]];foot=M(f'B_{s}_Foot');target=foot.translation.copy();target.z+=z-float(pts[:,2].min());leg(s,target,foot.to_3x3())
if __name__ == '__main__':
 # A single off-hand frame selected in the rest pose; never choose a new roll independently per sample.
 choices=[]
 for degrees in [5]:
  L=Matrix.Rotation(math.radians(degrees),3,'Z')@Hframe['L'];H=A0.to_3x3()@L;c=A0@Vector((0,0,gripz['L']));result,_=arm('L',c-H@Vector(G['L']['handle_centre_hand_local']),H);choices.append((result[0],degrees,L))
 # Passing hrot explicitly keeps the solve in the fixed weapon frame.
 best=min(choices,key=lambda v:v[0]);Hframe['L']=best[2];print('FIXED GRIP L',best[:2],flush=True)
 apply(source['plant'][0]);SR0=M('B_R_Hand').to_3x3();SC0=M('B_R_Hand')@Vector(G['R']['handle_centre_hand_local']);CHEST0=M('B_Spine2').to_3x3();CG0=A0@Vector((0,0,gripz['R']));
 axis_samples=json.loads((P/'work/round1_mixamo_grip.json').read_text());sa=sum((Vector(v['axis_target_local']) for v in axis_samples),Vector()).normalized();SRC_AR=AR.copy();SRC_AR=transform(Vector(G['R']['handle_axis_hand_local']).rotation_difference(sa).to_matrix()@AR.to_3x3(),Vector(G['R']['handle_centre_hand_local'])-sa*gripz['R'])
 stand=raw['Standing'][0];prepared={};axeTargets={};legnames=[n for n in names if any(x in n for x in ['Thigh','Calf','Foot','Toe'])]
 for nm in roles:
  pp=[];aa=[]
  if nm in ['Attack','Cast']:
   rows=source['plant']
   for i,pose in enumerate(rows):
    u=i/30;blend=smooth(u/.22)*smooth((N/30-u)/.25);apply(pose);sp=M('B_Spine');oldchest=M('B_Spine2');carrier=M('B_R_Hand')@SRC_AR
    row=mix(stand,pose,blend)
    for n in ['B_Pelvis']+legnames:row[n]=mix(stand,source['turn'][i],.2*blend)[n]
    apply(row);setmat('B_Spine',transform(stand['B_Spine'].to_3x3(),M('B_Spine').translation)) if False else None
    # Preserve the planted source torso while adding its small weight transfer.
    sourceSp=sp.to_quaternion();apply(stand);standingSp=M('B_Spine').to_quaternion();apply(row);setmat('B_Spine',transform(standingSp.slerp(sourceSp,blend).to_matrix(),M('B_Spine').translation))
    # Keep the library's sway and shoulder wind-up within this broad, short-necked body's range.
    spine=['B_Spine','B_Spine1','B_Spine2'];axes={n:(restb[n].inverted()@restb[c].translation).normalized() for n,c in zip(spine,['B_Spine1','B_Spine2','B_Neck'])}
    rolls={n:twist(stand[n].to_quaternion().inverted()@r.pose.bones[n].rotation_quaternion,axes[n]) for n in spine};total=sum(rolls.values());limit=math.radians(42)*math.tanh(total/math.radians(42));factor=limit/total if abs(total)>1e-6 else 1
    for n in spine:
     pb=r.pose.bones[n];q0=stand[n].to_quaternion();q=q0.inverted()@pb.rotation_quaternion;sw=q@Quaternion(axes[n],-rolls[n]);pb.rotation_quaternion=q0@Quaternion().slerp(sw,.75)@Quaternion(axes[n],rolls[n]*factor)
    update()
    for n in ['B_Neck','B_Head']:
     q0=stand[n].to_quaternion();r.pose.bones[n].rotation_quaternion=q0.slerp(r.pose.bones[n].rotation_quaternion,.45)
    update()
    # Left preparation step; one raised foot at a time, then plant for the release and recover.
    for s in 'RL':
     foot=home[s];target=foot.translation.copy()
     if s=='L':
      if u<.46:v=smooth((u-.14)/.32);lift=.09*math.sin(math.pi*v);target+=Vector((-.015,-.105,0))*v;target.z+=lift
      elif u<.92:target+=Vector((-.015,-.105,0))
      else:v=smooth((u-.92)/.30);target+=Vector((-.015,-.105,0))*(1-v);target.z+=.055*math.sin(math.pi*v)
     leg(s,target,foot.to_3x3());flatten(s,max(0,target.z-foot.translation.z))
    row=snapshot();rot=A0.to_quaternion().slerp(carrier.to_quaternion(),blend).to_matrix();loc=A0.translation.lerp(carrier.translation,blend);carrier=transform(rot,loc)
    pp.append(row);aa.append(carrier)
   if nm=='Cast':
    k=16;pp=pp[:k]+[pp[k]]*8+pp[k:];aa=aa[:k]+[aa[k]]*8+aa[k:]
  else:
   for row in raw[nm]:
    apply(row);aa.append(M('Axe')@axerest.inverted())
    if nm in ['Standing','Fidget']:
     for s in 'RL':flatten(s)
    pp.append(snapshot())
  prepared[nm]=pp;axeTargets[nm]=aa
 # Fit ONE grasp orientation to the complete motion set, with no per-frame roll selection.
 for nm,aa in axeTargets.items():
  for i,A in enumerate(aa):
   if nm!='Dead' and not (nm=='Death' and i/30>1/6):A.translation+=Vector((0,-.08,.05))
   if nm in ['Attack','Cast']:
    env=smooth(i/6)*smooth((len(aa)-1-i)/8);A.translation+=Vector((-.06,-.06,.04))*env
 calibration={}
 for side in 'RL':
  candidates=[]
  for angle in [0]:
   frame=Matrix.Rotation(math.radians(angle),3,'Z')@Hframe[side];scores=[];ext=[]
   for nm in ['Standing','Walking','Attack']:
    for i in range(0,len(prepared[nm]),4 if nm=='Attack' else 8):
     apply(prepared[nm][i]);A=axeTargets[nm][i];HR=A.to_3x3()@frame;c=A@Vector((0,0,gripz[side]));v,_=arm(side,c-HR@Vector(G[side]['handle_centre_hand_local']),HR);scores.append(v[0]);ext.append([abs(math.degrees(v[k])) for k in [4,5,6]])
   score=np.mean(scores)+2*max(scores);candidates.append((float(score),angle,frame,ext))
  best=min(candidates,key=lambda x:x[0]);Hframe[side]=best[2];calibration[side]={'angle_degrees':best[1],'limits':np.max(best[3],axis=0).tolist(),'curve':[[v[1],v[0]] for v in candidates]};print('GLOBAL GRIP',side,calibration[side],flush=True)
 AR=transform(Hframe['R'].inverted(),Vector(G['R']['handle_centre_hand_local'])-Hframe['R'].inverted()@Vector((0,0,gripz['R'])))
 (P/'review/round1/grip_calibration.json').write_text(json.dumps(calibration,indent=2))
 def carrier_cost(A,origin,zs):
  cost=8*(A.translation-origin).length_squared
  for sd in 'RL':
   HR=A.to_3x3()@Hframe[sd];target=A@Vector((0,0,zs[sd]))-HR@Vector(G[sd]['handle_centre_hand_local']);v,sh=arm(sd,target,HR);cost+=v[0];cost+=10000*max(0,(target-sh).length-(armdata[sd][3]+armdata[sd][4])*.96)**2
   cost+=100*max(0,abs(v[4])-math.radians(85))**2+100*max(0,v[5]-math.radians(52))**2
  torso=M('B_Pelvis').translation+Vector((0,-.035,.32));head=M('B_Head').translation+Vector((0,-.035,.04))
  for point in [A@Vector((x,0,z)) for x,z in [(0,.1),(0,.3),(0,.5),(0,.9),(0,1.15),(-.24,1.08),(.24,1.08)]]:
   for cen,rad3 in [(torso,Vector((.34,.29,.42))),(head,Vector((.34,.36,.34)))]:
    d=point-cen;inside=1-sum((d[k]/rad3[k])**2 for k in range(3));cost+=100*max(0,inside)**2
  return cost
 result={};metrics={}
 for nm,rows in prepared.items():
  out=[];stats=[];preferred={};deathpose=None
  for i,row in enumerate(rows):
   apply(row);A=axeTargets[nm][i].copy();
   zs=gripz.copy()
   held=nm!='Dead' and (nm!='Death' or i/30<=1/6)
   if held:
    if nm in ['Attack','Cast']:
     origin=A.translation.copy();best=carrier_cost(A,origin,zs)
     for step in [.08,.04,.02,.01]:
      for repeat in range(2):
       for axis in range(3):
        selected=A
        for sign in [-1,1]:
         test=A.copy();test.translation[axis]+=sign*step;value=carrier_cost(test,origin,zs)
         if value<best:best=value;selected=test
        A=selected
    # Retargeted arm lengths require a small carrier translation; orientation and momentum remain source-driven.
    for _ in range(16):
     move=Vector()
     for s in 'RL':
      HR=A.to_3x3()@Hframe[s];c=A@Vector((0,0,zs[s]));target=c-HR@Vector(G[s]['handle_centre_hand_local']);un,fn,hn,la,lb,*_=armdata[s];sh=M(un).translation;v=target-sh
      if v.length>(la+lb)*.96:move-=(v-v.normalized()*(la+lb)*.96)*.5
     A.translation+=move
     if move.length<.00001:break
    for s in 'RL':
     HR=A.to_3x3()@Hframe[s];c=A@Vector((0,0,zs[s]));target=c-HR@Vector(G[s]['handle_centre_hand_local']);stats.append([s,i]+solvearm(s,target,HR,preferred.get(s)));preferred[s]=M(f'B_{s}_Forearm').translation
     for n,q in G[s]['finger_local'].items():r.pose.bones[n].rotation_quaternion=Quaternion(q)
    update();setmat('Axe',M('B_R_Hand')@AR@axerest)
    if nm=='Death':deathpose=snapshot()
   elif nm=='Death' and i/30<.4:
    # Ease the released hands from the corrected grasp into the existing library fall.
    u=smooth((i/30-1/6)/.23)
    for n in names:
     if any(x in n for x in ['UpperArm','Forearm','Hand','Finger']):r.pose.bones[n].matrix_basis=mix(deathpose,row,u)[n]
    update();setmat('Axe',A@axerest)
   out.append(snapshot())
  result[nm]=out;metrics[nm]={'roll_swing_upper_max_deg':[max([abs(v[k]) for v in stats],default=0) for k in [2,3,4]],'samples':stats};print('FIT',nm,metrics[nm]['roll_swing_upper_max_deg'],flush=True)
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 for nm,rows in result.items():
  a=bpy.data.actions.new(nm);a.use_fake_user=True;prev={}
  for i,row in enumerate(rows):
   apply(row);r.animation_data.action=a
   for n in names:
    pb=r.pose.bones[n];q=pb.matrix_basis.to_quaternion()
    if n in prev and q.dot(prev[n])<0:q.negate()
    prev[n]=q.copy();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.scale=(1,1,1);pb.keyframe_insert('rotation_quaternion',frame=i);pb.keyframe_insert('location',frame=i)
   r.animation_data.action=None
  a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
  for la in a.layers:
   for st in la.strips:
    for cb in st.channelbags:
     for fc in cb.fcurves:
      for k in fc.keyframe_points:k.interpolation='LINEAR'
 (P/'review/round1/fit.json').write_text(json.dumps(metrics,indent=2));(P/'work/round1_grip_frames.json').write_text(json.dumps({'frames':{s:[list(v) for v in Hframe[s]] for s in 'RL'},'grip_z':gripz,'right_hand_to_axe':[list(v) for v in AR]},indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_fitted.blend'))
 common.workbench_clay(sc);sc.view_settings.view_transform='Standard'
 for nm in ['Standing','Attack','Cast','Fidget']:
  a=bpy.data.actions[nm]
  for i in range(7 if nm in ['Attack','Cast'] else 1):
   sample(a,a.frame_range[1]*i/6);common.render_views(str(P/f'review/round1/{nm}_{i}'),1,3.3,views=['front','left','three_quarter'],resolution=(420,480))
