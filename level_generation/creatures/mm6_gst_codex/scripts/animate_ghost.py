"""Native suspended claw swipe, owned hit recoil, and articulated shroud collapse."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=60
D=json.loads((P/'work/rig.json').read_text());B=D['bones'];R={n:rig.data.bones[n].matrix_local.copy() for n in B};REL={n:R[b['parent']].inverted()@R[n] if b['parent'] else R[n] for n,b in B.items()};J={n:Vector(v) for n,v in D['joints'].items()};SRC=json.loads((P/'work/source_rest.json').read_text());SOURCE=json.loads((P/'work/source_motion.json').read_text())['UnarmedGetHitF2'];C=np.array([v.co[:] for v in body.data.vertices]);E=np.array([e.vertices[:] for e in body.data.edges]);PA=np.array([v.value for v in body.data.attributes['part'].data]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1)
LOOPS={'Standing':3.,'Walking':1.4,'Running':1.,'Attack':1.4,'Hit':.75,'Fidget':3.,'Death':1.8,'Dead':1.}
def ss(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
def env(t,a,b,c):return ss((t-a)/(b-a))*(1-ss((t-b)/(c-b)))
def rot(axis,angle):return Quaternion(axis,angle)
def mat(q,p):m=q.to_matrix().to_4x4();m.translation=Vector(p);return m
def unit(v):return Vector(v).normalized()
def path(t,keys):
 if t<=keys[0][0]:return Vector(keys[0][1])
 for (a,p),(b,q) in zip(keys,keys[1:]):
  if t<=b:return Vector(p).lerp(Vector(q),ss((t-a)/(b-a)))
 return Vector(keys[-1][1])
def align_frame(rest_f,rest_p,f,p):
 def fr(a,b):
  a=unit(a);b=Vector(b)-a*a.dot(Vector(b));b.normalize();return Matrix((a,b,a.cross(b))).transposed()
 return (fr(f,p)@fr(rest_f,rest_p).transposed()).to_quaternion()
def pose(role,t):
 if role=='Dead':role,t='Death',LOOPS['Death']
 cyc=2*math.pi*t/LOOPS[role];gait=role in ('Walking','Running');run=role=='Running';attack=role=='Attack';death=role=='Death'
 wind=env(t,0,.40,.77) if attack else 0;strike=env(t,.40,.86,1.4) if attack else 0;hit=env(t,0,.17,.75) if role=='Hit' else 0;fidget=math.sin(cyc)*math.sin(cyc*.5)**2 if role=='Fidget' else 0;fall=ss((t-.35)/1.20) if death else 0;burst=env(t,0,.28,.72) if death else 0
 pitch=-.27*wind+.29*strike-.17*hit-.18*burst+( .12 if run else .06 if gait else 0)+.22*fall
 yaw=-.25*wind+.32*strike+.11*fidget;bank=.025*math.sin(cyc) if gait else -.17*wind+.17*strike
 q=rot((0,0,1),yaw)@rot((0,1,0),bank)@rot((1,0,0),pitch)
 base=J['Pelvis']+Vector((.025*math.sin(cyc) if gait else -.075*wind+.095*strike,.085*wind-.125*strike,.024*math.sin(cyc)*(1-fall)+.06*burst-1.12*fall))
 X=mat(q,base)@Matrix.Diagonal((1,1,1-.50*fall,1))@Matrix.Translation(-J['Pelvis']);M={'Root':R['Root'].copy(),'BodyRoot':mat(q@R['BodyRoot'].to_quaternion(),base)}
 k=min(max(t-.06,0),.5)*30;i=min(int(k),len(SOURCE['keys'])-1);j=min(i+1,len(SOURCE['keys'])-1)
 def source_delta(n):return Quaternion(SOURCE['keys'][i][n]['q']).slerp(Quaternion(SOURCE['keys'][j][n]['q']),k-i)@Matrix(SRC[n]['rot']).to_quaternion().inverted()
 for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
  m=M[B[n]['parent']]@REL[n]
  if fall:m.translation=(X@R[n]).translation
  if role=='Hit' and n in ('B_Spine','B_Spine1','B_Spine2'):m=mat(q@Quaternion().slerp(source_delta(n),.42*hit)@R[n].to_quaternion(),m.translation)
  if n=='B_Head':m=mat(q@rot((0,0,1),.25*fidget-.07*strike)@rot((1,0,0),-.30*fall+.04*wind)@rot((0,1,0),.38*fall)@R[n].to_quaternion(),m.translation)
  M[n]=m
 for sd,sign in [('L',1),('R',-1)]:
  clav='B_'+sd+'_Clavicle';M[clav]=M['B_Spine2']@REL[clav];upper='B_'+sd+'_UpperArm';fore='B_'+sd+'_Forearm';hand='B_'+sd+'_Hand'
  sh=(M[clav]@REL[upper]).translation;idle=Vector((sign*.485,-.205,1.545));target=idle+Vector((sign*.009*math.sin(cyc),-.014*math.sin(cyc),.015*math.sin(cyc)))
  pole=Vector((sign*.39,.045,1.69));finger=Vector((sign*.40,-.15,-1.));palm=Vector((0,-1,.1))
  if attack:
   if sd=='R':
    target=path(t,[(0,idle),(.40,(-.41,-.06,2.075)),(.55,(-.48,-.21,1.98)),(.78,(-.005,-.37,1.68)),(.933,(.15,-.32,1.51)),(1.4,idle)])
    pole=path(t,[(0,pole),(.40,(-.43,.075,1.83)),(.55,(-.48,-.035,1.86)),(.78,(-.29,-.18,1.70)),(.933,(-.22,-.10,1.61)),(1.4,pole)])
    finger=path(t,[(0,finger),(.40,(-.13,-.08,1)),(.55,(.2,-.15,.65)),(.78,(.60,-.30,-.80)),(.933,(.40,-.05,-1)),(1.4,finger)])
   else:
    # Support hand crosses the chest; its palm follows the forearm instead of folding backward.
    target=path(t,[(0,idle),(.40,(.045,-.31,1.79)),(.80,(.35,-.21,1.59)),(.933,(.42,-.16,1.54)),(1.4,idle)])
    pole=path(t,[(0,pole),(.40,(.37,.005,1.66)),(.80,(.39,.01,1.64)),(1.4,pole)])
    finger=path(t,[(0,finger),(.40,(-.80,-.28,.32)),(.80,(.40,-.10,-1)),(1.4,finger)])
  if gait:target+=Vector((sign*.018*math.sin(cyc),-.025-.015*run,.018*math.cos(cyc)))
  if hit:target=target.lerp(Vector((sign*.49,-.09,1.82)),hit);finger=finger.lerp(Vector((sign*.5,-.15,.7)),hit)
  if fidget:target+=Vector((sign*.045*fidget,-.04*fidget,.10*fidget*(1 if sd=='L' else -.3)))
  if death:target=target.lerp(Vector((sign*.48,-.03,1.96)),burst);finger=finger.lerp(Vector((sign*.5,-.1,.8)),burst)
  target=X@target;pole=X@pole;finger=q@finger;palm=q@palm
  if fall:
   target=target.lerp(Vector((sign*.39,-.16,.25 if sd=='L' else .39)),fall);pole=pole.lerp(Vector((sign*.43,.015,.39)),fall);finger=finger.lerp(Vector((sign*.55,-.45,.60)),fall);palm=palm.lerp(Vector((0,-1,.15)),fall)
  # Fixed-length arm IK; the pole controls the elbow plane rather than moving the joint independently.
  a=(J[sd+'_Forearm']-J[sd+'_UpperArm']).length;b=(J[sd+'_Hand']-J[sd+'_Forearm']).length;d=target-sh;length=min(max(d.length,abs(a-b)+.006),a+b-.008);direction=d.normalized();target=sh+direction*length
  u=pole-sh;u=(u-direction*u.dot(direction)).normalized();along=(a*a-b*b+length*length)/(2*length);el=sh+direction*along+u*math.sqrt(max(0,a*a-along*along))
  rn=(J[sd+'_Forearm']-J[sd+'_UpperArm']).cross(J[sd+'_Hand']-J[sd+'_Forearm']);wn=(el-sh).cross(target-el)
  for n,start,end,rstart,rend in [(upper,sh,el,J[sd+'_UpperArm'],J[sd+'_Forearm']),(fore,el,target,J[sd+'_Forearm'],J[sd+'_Hand'])]:M[n]=mat(align_frame(rend-rstart,rn,end-start,wn)@R[n].to_quaternion(),start)
  if attack:
   # Limit the visible wrist bend around the measured forearm-to-palm direction.
   fore_dir=unit(target-el);finger=unit(finger);swing=fore_dir.rotation_difference(finger)
   if swing.angle>math.radians(45):finger=Quaternion().slerp(swing,math.radians(45)/swing.angle)@fore_dir
  rest_f=Vector(D['digits'][sd+'2']['pts'][0])-J[sd+'_Hand'];rest_p=rest_f.cross(Vector(D['digits'][sd+'1']['pts'][0])-Vector(D['digits'][sd+'4']['pts'][0]));rest_p*=1 if rest_p.y<0 else -1;hq=align_frame(rest_f,rest_p,finger,palm);M[hand]=mat(hq@R[hand].to_quaternion(),target)
  for f in range(5):
   for idx,n in enumerate(D['digits'][sd+str(f)]['bones']):
    m=M[B[n]['parent']]@REL[n];curl=(.07+.12*wind+.06*hit)*(1-.7*fall) if f else .03;m=m@Matrix.Rotation(curl,4,'X');M[n]=m
 # Sleeves hang below the moving upper arm instead of inheriting its upward swing.
 for c in D['sleeves']:
  sd=c['side'];n0=c['bones'][0];anchor=M['B_'+sd+'_UpperArm']@R['B_'+sd+'_UpperArm'].inverted()@Vector(c['pts'][0]);prev=anchor
  for k,n in enumerate(c['bones']):
   rdir=Vector(c['pts'][k+1])-Vector(c['pts'][k]);sway=.06*math.sin(cyc-k*.45)+.11*strike-.08*wind;direction=unit((.04*(1 if sd=='L' else -1),sway,-1));length=rdir.length;end=prev+direction*length
   if attack:
    direction=q@direction;end=prev+direction*length
    # The sleeve is joined to the robe: lower cloth follows that seam as the arm crosses the chest.
    end=end.lerp(X@Vector(c['pts'][k+1]),(.40+.25*k)*max(wind,strike))
   if fall:
    final=Vector(((1 if sd=='L' else -1)*(.34+.055*k),-.08+.19*k,.12-.033*k));end=end.lerp(final,fall)
   dq=rdir.rotation_difference(end-prev);M[n]=mat(dq@R[n].to_quaternion(),prev);prev=end
 for c in D['cloth']:
  ang=c['angle'];prev=None
  for k,n in enumerate(c['bones']):
   m=X@R[n];phase=cyc-k*.55+ang*.25;amp=(.030 if gait else .018)+.028*burst
   dq=q@rot((1,0,0),amp*math.sin(phase)+(.045 if run else .025 if gait else 0)+.085*strike-.065*wind)@rot((0,1,0),amp*.45*math.cos(phase+ang));m=mat(dq@R[n].to_quaternion(),m.translation)
   if fall:
    rh=R[n].translation;h=Vector((rh.x*1.02,.075+(rh.y-.075)*.78+[0,.04,.12,.22,.34][k],[.18,.13,.10,.065,.045][k]));dq=rot((1,0,0),1.43);full=mat(dq@R[n].to_quaternion(),h);join=X@R[n];amount=min(1.,k*.45);target=mat(join.to_quaternion().slerp(full.to_quaternion(),amount),join.translation.lerp(h,amount));m=mat(m.to_quaternion().slerp(target.to_quaternion(),fall),m.translation.lerp(target.translation,fall))
   M[n]=m@Matrix.Diagonal((1,1-.50*fall,1,1))
 if death and fall:
  # As the arms release the garment, its sleeves settle with the adjacent shroud panels.
  def cloth_point(p):
   if p.z>1.51:return X@p
   tx=np.clip((p.x+.60)/1.20,0,1);ty=np.clip((p.y+.25)/.95,0,1);shares=[(1-tx)*(1-ty),tx*(1-ty),tx*ty,(1-tx)*ty];out=Vector()
   for chain,share in zip(D['cloth'],shares):
    levels=np.array([v[2] for v in chain['pts']]);z=(levels[:-1]+levels[1:])/2
    for k,bone in enumerate(chain['bones']):out+=(M[bone]@R[bone].inverted()@p)*float(share*np.interp(p.z,z[::-1],np.eye(5)[k][::-1]))
   return out.lerp(X@p,ss((p.z-1.40)/.11))
  for c in D['sleeves']:
   for k,n in enumerate(c['bones']):
    p=Vector(c['pts'][k]);h=cloth_point(p);eps=.003;axes=[Vector((eps,0,0)),Vector((0,eps,0)),Vector((0,0,eps))];jac=Matrix([(cloth_point(p+d)-cloth_point(p-d))/(2*eps) for d in axes]).transposed();target=(jac@R[n].to_3x3()).to_4x4();target.translation=h;old=M[n];amount=ss(min(1,fall*2.8));scale=old.to_scale().lerp(target.to_scale(),amount);M[n]=mat(old.to_quaternion().slerp(target.to_quaternion(),amount),old.translation.lerp(h,amount))@Matrix.Diagonal((*scale,1))
 M['Jaw']=M['B_Head']@REL['Jaw']@Matrix.Rotation(.09*wind+.16*strike+.08*hit+.20*burst,4,'X')
 for n,b in B.items():
  par=b['parent'];rig.pose.bones[n].matrix_basis=REL[n].inverted()@(M[par].inverted()@M[n] if par else M[n])
 bpy.context.view_layer.update()
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();low=min(v.co.z for v in mesh.vertices);ev.to_mesh_clear()
 if low<.008 or fall:rig.pose.bones['Root'].location+=R['Root'].to_3x3().transposed()@Vector((0,0,(.008-low)*(1 if low<.008 else fall)));bpy.context.view_layer.update()
 return M
rig.animation_data_clear()
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
pilot='--full' not in sys.argv;roles=['Standing','Walking','Attack','Hit','Death','Dead'] if pilot else list(LOOPS);reports={}
for role in roles:
 dur=LOOPS[role];count=round(dur*60);keys={n:[] for n in B};mins=[];ratios=[];first=None;wrist=[]
 for f in range(count+1):
  rig.animation_data_clear();M=pose(role,f/60);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();first=c.copy() if first is None else first;mins.append(float(c[:,2].min()));length=np.linalg.norm(c[E[:,1]]-c[E[:,0]],axis=1);mask=(PA[E[:,0]]==0)&(EL>.002);stretch=length[mask]/EL[mask];ratios.append([float(np.percentile(stretch,99)),float(stretch.max()),float((length-EL).max())]);wrist.append(list(M['B_R_Hand'].translation))
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
 reports[role]={'duration':count/60,'min_z':min(mins),'cloth_stretch_p99_max_growth':np.max(ratios,axis=0).tolist(),'loop_delta':float(np.linalg.norm(c-first,axis=1).max()),'cloth_p99_worst_time':int(np.argmax(np.array(ratios)[:,0]))/60,'cloth_edge_worst_time':int(np.argmax(np.array(ratios)[:,1]))/60,'right_wrist':wrist};print(role,{k:v for k,v in reports[role].items() if k!='right_wrist'},flush=True)
 common.workbench_clay(sc)
 frames=[0,round(count*.2),round(count*.4),round(count*.6),round(count*.8),count] if role in ('Attack','Death') else [0,round(count*.33),round(count*.66)]
 for f in frames:
  sc.frame_set(f+1);common.render_views(str(P/'review'/f'clay_{role}_{f:03}'),1.1,2.7,views=('front','left'),resolution=(400,540))
(P/'work/animation_audit.json').write_text(json.dumps(reports,indent=2));rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/('work/pilot_v1.blend' if pilot else 'work/anim_v1.blend')))
assert all(v['min_z']>.007 for v in reports.values()),'Floor gate failed'
assert all(reports[n]['loop_delta']<1e-4 for n in ['Standing','Walking','Dead']), 'Loop gate failed'

assert all(v['cloth_stretch_p99_max_growth'][0]<2.0 and v['cloth_stretch_p99_max_growth'][1]<4.6 for v in reports.values()),'Cloth deformation gate failed'
