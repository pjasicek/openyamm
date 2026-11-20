"""Review 2: rest-shape correction and anatomically hinged arms; authored two-hand staff thrust."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
# Read the inspected local staff clip for restrained torso drive; hands and discrete feet are fitted below.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(p.parents[2]/'anim_library/humanoid_set/2Hand Staff.glb'))
src=next(o for o in bpy.data.objects if o.type=='ARMATURE');act=next(a for a in bpy.data.actions if a.name.endswith('StaffAttack6'));src.animation_data.action=act;src.animation_data.action_slot=act.slots[0]
source=[];turn=Matrix.Rotation(math.pi,3,'Z')
for f in range(37):
 bpy.context.scene.frame_set(int(act.frame_range[0])+f)
 source.append({n:src.pose.bones[n].matrix_basis.to_3x3() for n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']})
bpy.ops.wm.open_mainfile(filepath=str(p/'review/round2/baseline/work/production_master.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];scene=bpy.context.scene;scene.render.fps=120
names=[b.name for b in rig.data.bones];robe=[n for n in names if n.startswith('Robe_')]
def attach(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 attach(None)
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 attach(a);scene.frame_set(int(f),subframe=float(f%1));return {n:rig.pose.bones[n].matrix_basis.copy() for n in names}
def setpose(d):
 attach(None)
 for n,m in d.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def smooth(t):
 t=max(0.,min(1.,t));return t*t*(3-2*t)
def curve(keys,t):
 if t<=keys[0][0]:return Vector(keys[0][1])
 for (a,x),(b,y) in zip(keys,keys[1:]):
  if a<=t<=b:return Vector(x).lerp(Vector(y),smooth((t-a)/(b-a)))
 return Vector(keys[-1][1])
old={r:bpy.data.actions[r] for r in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']}
base={r:[sample(a,f) for f in range(round(a.frame_range[1])+1)] for r,a in old.items()}
setpose({n:Matrix() for n in names})
# Widen shoulder joints and translate each intact arm/hand; UVs, topology and weights remain identical.
shift=.035;groups=[g.name for g in body.vertex_groups];moved=[]
for v in body.data.vertices:
 part=body.data.attributes['piece'].data[v.index].value
 if part==2:continue
 before=v.co.copy();x,y,z=v.co
 if part==100:
  fx=float(np.interp(z,[.12,.30,.55,.80,1.00,1.09],[.88,.85,.82,.86,1.0,1.10]));fy=float(np.interp(z,[.12,.55,.85,1.09],[.94,.90,.91,1.05]));v.co.x*=fx;v.co.y=(y+.02)*fy-.02
 elif part not in [101,102,103,104]:
  ar={s:sum(g.weight for g in v.groups if groups[g.group].startswith('B_'+s+'_') and any(k in groups[g.group] for k in ['UpperArm','Forearm','Hand','Finger'])) for s in 'LR'}
  aw=ar['L']+ar['R'];v.co.x+=shift*(ar['L']-ar['R'])
  # Broad chest and a modest waist; avoid the separate high collar and central neck trim.
  w=smooth((z-1.02)/.18)*(1-smooth((z-1.42)/.045))
  v.co.x+=x*.20*w*(1-aw)
  if 1.02<z<1.18:v.co.x+=x*.10*(1-w)*(1-aw)
 if (v.co-before).length>1e-7:moved.append((v.co-before).length)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for s,sgn in [('L',1),('R',-1)]:
 root=rig.data.edit_bones['B_'+s+'_UpperArm'];chain=[root,*root.children_recursive]
 for b in chain:b.head.x+=sgn*shift;b.tail.x+=sgn*shift
 # Upper-arm twist can be parented to the clavicle instead of its deform bone.
 n='B_'+s+'_UpperArmTwist'
 if rig.data.edit_bones[n] not in chain:rig.data.edit_bones[n].head.x+=sgn*shift;rig.data.edit_bones[n].tail.x+=sgn*shift
 rig.data.edit_bones['B_'+s+'_Clavicle'].tail.x+=sgn*shift
bpy.ops.object.mode_set(mode='OBJECT')
for v in staff.data.vertices:v.co.x-=shift
bpy.context.view_layer.update()
# Fit the existing rounded boot soles to a flat standing contact; retain upper leather, UVs and weights.
setpose(base['Standing'][0]);sole_vertices={};sole_changes=[]
for part,sd in [(101,'R'),(102,'L')]:
 ids=[v.index for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value==part]
 n='B_'+sd+'_Foot';D=rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted();inv=D.inverted();zmin=min((D@body.data.vertices[i].co).z for i in ids)
 for i in ids:
  v=body.data.vertices[i];co=D@v.co;z=co.z
  if z<.035:co.z=.004+(z-zmin)*.12
  elif z<.08:co.z=(.004+(.035-zmin)*.12)+((z-.035)/.045)*(.08-(.004+(.035-zmin)*.12))
  if abs(z-co.z)>1e-7:sole_changes.append(abs(z-co.z));v.co=inv@co
 sole_vertices[sd]=[rig.data.bones[n].matrix_local.inverted()@body.data.vertices[i].co for i in ids]
(p/'work/round2_soles.json').write_text(json.dumps({'vertices_changed':len(sole_changes),'max_displacement_mm':max(sole_changes)*1000,'idle_fidget_feet':'planted at the corrected Standing sole contact','upper_boots_uv_weights_preserved':True},indent=2))
import arm_solver as sol
right=sol.Side('B_R_');left=sol.Side('B_L_');G=sol.G
# Mirror the fitted right fist deformation onto the already fitted left finger chains.
setpose({n:Matrix() for n in names})
for n,q in G['finger_local'].items():rig.pose.bones[n].rotation_quaternion=q
bpy.context.view_layer.update();F=Matrix.Diagonal((-1.,1.,1.));leftfinger={}
for n in G['finger_local']:
 ln=n.replace('B_R_','B_L_').replace('Finger0.00','Finger0');D=rig.pose.bones[n].matrix.to_3x3()@rig.data.bones[n].matrix_local.to_3x3().inverted();R=F@D@F@rig.data.bones[ln].matrix_local.to_3x3();M=R.to_4x4();M.translation=rig.pose.bones[ln].head;rig.pose.bones[ln].matrix=M;bpy.context.view_layer.update();leftfinger[ln]=rig.pose.bones[ln].rotation_quaternion.copy()
Hr=rig.data.bones['B_R_Hand'].matrix_local;Hl=rig.data.bones['B_L_Hand'].matrix_local
left.grip_hand=Hl.inverted()@(F@(Hr@Vector(G['handle_centre_hand_local'])))
left.axis_hand=(Hl.to_3x3().inverted()@F@Hr.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
(p/'work/round2_left_grip.json').write_text(json.dumps({'centre':list(left.grip_hand),'axis':list(left.axis_hand),'world_centre':list(Hl@left.grip_hand),'world_axis':list(Hl.to_3x3()@left.axis_hand),'fingers':{n:list(q) for n,q in leftfinger.items()}},indent=2))
from sleeve_fit_r2 import Sleeve
sleeves={side.s:Sleeve(rig,body,side.s) for side in [left,right]}
twist_state={}
def wrist(side,W,pole,Rh=None):
 S=rig.pose.bones[side.s+'UpperArm'].head.copy();E,W2=side.ik(S,W,pole);u=(E-S).normalized();f=(W2-E).normalized()
 Ra=rig.pose.bones[side.s+'Clavicle'].matrix.to_3x3()@side.rel['UpperArm'];Ra=(Ra@side.uA).rotation_difference(u).to_matrix()@Ra
 h=Ra@side.hinge_local();normal=u.cross(f).normalized();angle=math.atan2(h.cross(normal).dot(u),h.dot(normal));Ra=Quaternion(u,angle).to_matrix()@Ra
 Rf=Ra@side.rel['Forearm'];Rf=(Rf@side.uF).rotation_difference(f).to_matrix()@Rf
 if Rh is None:Rh=Rf@side.rel['Hand']
 else:
  tw=sol.swing_twist_deg(((Rf@side.rel['Hand']).inverted()@Rh).to_quaternion(),Vector((0,1,0)))[1]
  if side.s in twist_state:
   while tw-twist_state[side.s]>180:tw-=360
   while tw-twist_state[side.s]<-180:tw+=360
  twist_state[side.s]=tw;Rf=Quaternion(f,math.radians(max(-85,min(85,tw)))).to_matrix()@Rf
 side.apply(dict(S=S,E=E,W=W2,Ra=Ra,Rf=Rf,Rh=Rh))
 error=(W-W2).length
 if error>worst.get('miss_m',0):worst.update(side=side.s,time=t,miss_m=error,wrist=list(W),shoulder=list(S))
 return error
def choose_grip(side,C,A,pole,previous):
 sleeves[side.s].begin()
 best=None;q0=(side.rest['Hand']@side.axis_hand).rotation_difference(A).to_matrix();S=rig.pose.bones[side.s+'UpperArm'].head.copy();baseR=rig.pose.bones[side.s+'Clavicle'].matrix.to_3x3()@side.rel['UpperArm']
 angles=[-90,-60,-30,0,30,60,90] if previous is None else [max(-120,min(120,previous['pole_angle']+d)) for d in [-8,-4,0,4,8]]
 for angle in angles:
  P=Quaternion((C-S).normalized(),math.radians(angle))@pole
  if side.s=='B_R_':P=restPole.lerp(P,smooth(t/.20)*smooth((1.75-t)/.33))
  phis=[2*math.pi*k/72 for k in range(72)] if previous is None else [previous['phi']+math.radians(d) for d in [-8,-4,0,4,8]]
  for phi in phis:
   Rh=Quaternion(A,phi).to_matrix()@q0@side.rest['Hand']
   if side.s=='B_R_':Rh=restRh.slerp(Rh.to_quaternion(),smooth(t/.20)*smooth((1.75-t)/.33)).to_matrix()
   r=side.pose_anatomical(C,Rh,P,prev_tw=twist_state.get(side.s))
   u=(r['E']-r['S']).normalized();v=(r['W']-r['E']).normalized();bend=math.degrees(u.angle(v));minimal=(baseR@side.uA).rotation_difference(u).to_matrix()@baseR;q=(r['Ra']@minimal.inverted()).to_quaternion();humerus=(math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).dot(u),q.w))+180)%360-180
   shaft_angle=math.degrees(v.angle(A));sign=1 if side.s=='B_L_' else -1;medial=max(0,.17-sign*r['E'].x)
   cost=r['miss']*30000+r['sw']+.5*abs(r['tw'])+.10*abs(humerus)+5*max(0,abs(humerus)-55)+6*max(0,75-shaft_angle)+4*max(0,shaft_angle-115)+10*max(0,bend-145)+medial*2000+max(0,.035-sign*(r['W'].x-C.x))*1500+max(0,.07*math.sqrt(max(0,1-A.z*A.z))-(C.z-r['W'].z))*15000+max(0,r['E'].z-r['W'].z+.06)*6000*math.sqrt(max(0,1-A.z*A.z))
   cost+=300000*sleeves[side.s].cost(r,C,Rh@side.axis_hand,helper_twist)+5000*max(0,sleeves[side.s].stretch-1.85)
   if previous is not None:cost+=.30*math.degrees(abs((phi-previous['phi']+math.pi)%(2*math.pi)-math.pi))+.30*abs(angle-previous['pole_angle'])
   if best is None or cost<best['score']:r.update(score=cost,phi=phi,pole_angle=angle,pole=P,humerus=humerus,shaft_angle=shaft_angle);best=r
 return best
# Leg IK keeps the foot orientation and knee plane independent of imported knee pops.
def leg(sd,target,pole=None):
 up,lo,foot=[rig.pose.bones[f'B_{sd}_{n}'] for n in ['Thigh','Calf','Foot']];A=up.head.copy();W=target.translation;L1=(rig.data.bones[lo.name].head_local-rig.data.bones[up.name].head_local).length;L2=(rig.data.bones[foot.name].head_local-rig.data.bones[lo.name].head_local).length
 d=W-A;dist=min(d.length,(L1+L2)*.999);u=d.normalized();q=(L1*L1+dist*dist-L2*L2)/(2*dist);pole=Vector((0,-1,0)) if pole is None else pole;pole=(pole-u*pole.dot(u)).normalized();E=A+u*q+pole*math.sqrt(max(0,L1*L1-q*q));W2=A+u*dist
 for pb,dst,child in [(up,E,lo),(lo,W2,foot)]:
  R=(child.head-pb.head).normalized().rotation_difference((dst-pb.head).normalized()).to_matrix()@pb.matrix.to_3x3();M=R.to_4x4();M.translation=pb.head;pb.matrix=M;bpy.context.view_layer.update()
 M=target.copy();M.translation=W2;foot.matrix=M;bpy.context.view_layer.update()
stand=base['Standing'][0];setpose(stand);feet={s:rig.pose.bones['B_'+s+'_Foot'].matrix.copy() for s in 'LR'};pelvis0=rig.pose.bones['B_Pelvis'].head.copy();grip0=rig.pose.bones['B_R_Hand'].matrix@Vector(G['handle_centre_hand_local']);axis0=(rig.pose.bones['B_R_Hand'].matrix.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
restRh=rig.pose.bones['B_R_Hand'].matrix.to_quaternion();restPole=rig.pose.bones['B_R_Forearm'].head-rig.pose.bones['B_R_UpperArm'].head
standRoot=rig.pose.bones['B_Spine'].matrix.copy();freeLocal=standRoot.inverted()@Vector((.31,-.075,.958))
N={r:len(v)-1 for r,v in base.items()};N['Attack']=216
for r,a in old.items():a.name='Previous_'+r;a.use_fake_user=False
report={};intent=[];rest_fixed=None
for role in N:
 out=bpy.data.actions.new(role);out.use_fake_user=True;out.use_frame_range=True;out.frame_start=0;out.frame_end=N[role];miss=0.;prevphi=None;leftphi=None;twist_state.clear();helper_twist={};left_delta=None;worst={}
 for f in range(N[role]+1):
  t=f/120;d=stand if role=='Attack' else base[role][f];setpose(d)
  if role!='Attack':
   for sd in 'LR':
    M=feet[sd].copy() if role in ['Standing','Fidget'] else rig.pose.bones['B_'+sd+'_Foot'].matrix.copy()
    floor=min((M@v).z for v in sole_vertices[sd]);lift=max(0,.004-floor);M.translation.z+=lift
    if role in ['Standing','Fidget']:leg(sd,M)
    elif lift>1e-6:leg(sd,M,rig.pose.bones['B_'+sd+'_Calf'].head-rig.pose.bones['B_'+sd+'_Thigh'].head)
  if role=='Attack':
   rawrobe={n:rig.pose.bones[n].matrix.copy() for n in robe}
   before={n:rig.pose.bones[n].head.copy() for n in ['B_Pelvis',*[f'B_{s}_{b}' for s in 'LR' for b in ['Calf','Foot']]]}
   sf=max(0,min(36,round((t-.25)*30)));influence=.20*smooth(t/.25)*smooth((1.65-t)/.25)
   for n in source[0]:
    D=source[0][n].inverted()@source[sf][n];rig.pose.bones[n].rotation_quaternion=stand[n].to_quaternion()@Quaternion().slerp(D.to_quaternion(),influence);bpy.context.view_layer.update()
   lean=math.radians(7)*smooth(t/.50)*smooth((1.4-t)/.35)
   turn=math.radians(-50)*smooth(t/.45)*smooth((1.48-t)/.40)
   for n in ['B_Spine','B_Spine1','B_Spine2']:
    M=rig.pose.bones[n].matrix.copy();R=Quaternion((0,0,1),turn/3).to_matrix()@Quaternion((1,0,0),lean/3).to_matrix()@M.to_3x3();newM=R.to_4x4();newM.translation=M.translation;rig.pose.bones[n].matrix=newM;bpy.context.view_layer.update()
   for n in ['B_Neck','B_Head']:
    M=rig.pose.bones[n].matrix.copy();R=Quaternion((0,0,1),-turn/2).to_matrix()@M.to_3x3();Q=R.to_4x4();Q.translation=M.translation;rig.pose.bones[n].matrix=Q;bpy.context.view_layer.update()
   # Ready, gather the lower shaft with the free hand, drive the crown forward, recover.
   motion=curve([(0,(0,0,0)),(.28,(0,.018,-.01)),(.72,(0,-.16,-.045)),(1.0,(0,-.15,-.035)),(1.65,(0,0,0)),(1.8,(0,0,0))],t)
   M=rig.pose.bones['B_Pelvis'].matrix.copy();M.translation+=motion;rig.pose.bones['B_Pelvis'].matrix=M;bpy.context.view_layer.update()
   for sd in 'LR':
    M=feet[sd].copy()
    if sd=='R':M.translation+=curve([(0,(0,0,0)),(.25,(0,0,0)),(.40,(0,-.085,.042)),(.55,(0,-.17,0)),(1.05,(0,-.17,0)),(1.23,(0,-.085,.042)),(1.42,(0,0,0)),(1.8,(0,0,0))],t)
    leg(sd,M)
   after={n:rig.pose.bones[n].head.copy() for n in before}
   for n in robe:
    z=rig.data.bones[n].head_local.z;x=rig.data.bones[n].head_local.x;mix=max(0,min(1,.5+x/.40))
    dp=after['B_Pelvis']-before['B_Pelvis'];dk=(after['B_R_Calf']-before['B_R_Calf']).lerp(after['B_L_Calf']-before['B_L_Calf'],mix);df=(after['B_R_Foot']-before['B_R_Foot']).lerp(after['B_L_Foot']-before['B_L_Foot'],mix)
    shiftcloth=df.lerp(dk,max(0,min(1,(z-.10)/.48))) if z<.58 else dk.lerp(dp,max(0,min(1,(z-.58)/.46)))
    M=rawrobe[n].copy();M.translation+=shiftcloth;rig.pose.bones[n].matrix=M;bpy.context.view_layer.update()
   gp=curve([(0,grip0),(.20,(-.43,-.25,1.36)),(.40,(-.33,-.15,1.36)),(.55,(-.28,-.24,1.36)),(.62,(-.28,-.24,1.36)),(.82,(-.28,-.33,1.36)),(1.02,(-.28,-.32,1.36)),(1.23,(-.33,-.15,1.36)),(1.48,(-.43,-.25,1.36)),(1.75,grip0),(1.8,grip0)],t)
   ax=curve([(0,axis0),(.20,(.25,-.55,.8)),(.40,(.22,-.975,0)),(1.23,(.22,-.975,0)),(1.48,(.25,-.55,.8)),(1.75,axis0),(1.8,axis0)],t).normalized()
   poleR=Vector((-.4,-1,-.3))
   # Coarse roll search here is continuous in the following anatomical solve.
   r=choose_grip(right,gp,ax,poleR,prevphi);prevphi={'phi':r['phi'],'pole_angle':r['pole_angle']};Rh=r['Rh'];W=gp-Rh@right.grip_hand
   miss=max(miss,wrist(right,W,r['pole'],Rh))
   gp=rig.pose.bones['B_R_Hand'].matrix@right.grip_hand;ax=(rig.pose.bones['B_R_Hand'].matrix.to_3x3()@right.axis_hand).normalized()
   # The second hand takes a lower shaft grip, with thumb toward the head, through the thrust.
   weight=smooth((t-.26)/.30)*smooth((1.20-t)/.18);cp=gp+ax*.26
   lr=choose_grip(left,cp,ax,Vector((.4,-1,-.3)),leftphi);leftphi={'phi':lr['phi'],'pole_angle':lr['pole_angle']}
   relaxed=curve([(0,(.31,-.075,.958)),(.40,(.32,-.40,1.44)),(.90,(.30,-.45,1.40)),(1.02,(.30,-.45,1.40)),(1.20,(.32,-.40,1.40)),(1.42,(.34,-.10,1.02)),(1.65,(.31,-.075,.958)),(1.8,(.31,-.075,.958))],t)+motion
   W=relaxed.lerp(cp-lr['Rh']@left.grip_hand,weight)
   # At full grip the hand follows the shaft exactly; gather/release blends in palm rotation.
   basePole=Vector((.15,1,-.1)).lerp(Vector((1,0,-.4)),smooth(t/.26)*smooth((1.65-t)/.30));leftPole=basePole.lerp(lr['pole'],weight)
   neutral=freeHandWorld;dq=neutral.inverted()@lr['Rh'].to_quaternion()
   if (left_delta is not None and dq.dot(left_delta)<0) or (left_delta is None and dq.w<0):dq.negate()
   left_delta=dq.copy();v=Vector((dq.x,dq.y,dq.z));angle=2*math.atan2(v.length,dq.w);Rh=(neutral@Quaternion(v.normalized() if v.length>1e-8 else Vector((0,1,0)),angle*weight)).to_matrix()
   miss=max(miss,wrist(left,W,leftPole,Rh))
   for n,q in leftfinger.items():rig.pose.bones[n].rotation_quaternion=Quaternion().slerp(q,weight)
   intent.append({'t':t,'right_grip':list(gp),'axis':list(ax),'left_grip':list(cp),'left_grip_weight':weight})
  else:
   # Re-solve both elbow planes. Preserve the staff's exact hand pose and all existing secondary motion.
   H=rig.pose.bones['B_R_Hand'].matrix.copy();E=rig.pose.bones['B_R_Forearm'].head.copy();S=rig.pose.bones['B_R_UpperArm'].head.copy();miss=max(miss,wrist(right,H.translation,E-S,H.to_3x3()))
   H=rig.pose.bones['B_L_Hand'].matrix.copy();delta=rig.pose.bones['B_Pelvis'].head-pelvis0
   if role in ['Standing','Walking']:
    W=Vector((.31,-.075,.958))+delta
    if role=='Walking':W.x+=.018;W.y+=.028*math.sin(2*math.pi*f/N[role])
    miss=max(miss,wrist(left,W,Vector((.15,1,-.1))))
   elif role in ['Cast','Hit']:
    miss=max(miss,wrist(left,H.translation,Vector((.30,.6,-1))))
   elif role=='Fidget':miss=max(miss,wrist(left,H.translation,Vector((.35,.55,-1)),H.to_3x3()))
   elif role in ['Death','Dead']:
    M=rig.pose.bones['B_Spine'].matrix;W=(M@freeLocal).lerp(H.translation,smooth(t/.35));W.z+=.025*smooth((t-.35)/.25);pole=M.to_3x3()@standRoot.to_3x3().inverted()@Vector((.15,1,-.1));miss=max(miss,wrist(left,W,pole))
   else:
    E=rig.pose.bones['B_L_Forearm'].head.copy();S=rig.pose.bones['B_L_UpperArm'].head.copy();miss=max(miss,wrist(left,H.translation,E-S,H.to_3x3()))
  for n,q in G['finger_local'].items():rig.pose.bones[n].rotation_quaternion=q
  for sd in 'LR':
   fb,hb=[rig.data.bones[f'B_{sd}_{b}'] for b in ['Forearm','Hand']];axis=(fb.matrix_local.inverted()@hb.head_local).normalized();dq=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion()@(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion().inverted()
   def twist(q,a):return (2*math.atan2(Vector((q.x,q.y,q.z)).dot(a),q.w)+math.pi)%(2*math.pi)-math.pi
   n=f'B_{sd}_ForearmTwist';a=twist(dq,axis)
   if n in helper_twist:a+=round((helper_twist[n]-a)/(2*math.pi))*2*math.pi
   helper_twist[n]=a;rig.pose.bones[n].rotation_quaternion=Quaternion(axis,.5*a)
   ub=rig.data.bones[f'B_{sd}_UpperArm'];axis=(ub.matrix_local.inverted()@fb.head_local).normalized();n=f'B_{sd}_UpperArmTwist';a=twist(rig.pose.bones[ub.name].matrix_basis.to_quaternion(),axis)
   if n in helper_twist:a+=round((helper_twist[n]-a)/(2*math.pi))*2*math.pi
   helper_twist[n]=a;rig.pose.bones[n].rotation_quaternion=Quaternion(axis,-.5*a)
  bpy.context.view_layer.update();pose={n:rig.pose.bones[n].matrix_basis.copy() for n in names}
  if role=='Standing' and f==0:rest_fixed={n:m.copy() for n,m in pose.items()};freeHandWorld=rig.pose.bones['B_L_Hand'].matrix.to_quaternion()
  attach(out)
  for n,m in pose.items():
   pb=rig.pose.bones[n];pb.matrix_basis=m;pb.rotation_mode='QUATERNION';pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis' or n in robe:pb.keyframe_insert('location',frame=f)
  attach(None)
 report[role]={'frames':N[role]+1,'arm_target_miss_mm':miss*1000,'worst':worst};print('ROUND2',role,report[role],flush=True)
for a in list(bpy.data.actions):
 if a.name.startswith('Previous_'):bpy.data.actions.remove(a)
setpose({n:Matrix() for n in names})
(p/'work/round2_motion.json').write_text(json.dumps(report,indent=2));(p/'work/round2_attack_intent.json').write_text(json.dumps(intent))
(p/'work/round2_shape.json').write_text(json.dumps({'shoulder_joint_outward_mm':shift*1000,'vertices_changed':len(moved),'max_displacement_mm':max(moved)*1000,'topology_uv_weights_preserved':True,'face_collar_preserved':True},indent=2))
import runpy
runpy.run_path(str(p/'scripts/normalize_keys_r2.py'))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round2_motion.blend'))
