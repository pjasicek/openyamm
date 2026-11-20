"""Mage ready/casting pilot, retaining the reviewed Ogre locomotion and the selected cast's body action."""
from pathlib import Path
import bpy,sys,math,json,ast,numpy as np
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
import common,armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_wand.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
scene.render.fps=30;names=[b.name for b in rig.data.bones]
def set_act(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 set_act(a);scene.frame_set(int(f),subframe=f-int(f))
 return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def apply(pose):
 set_act(None)
 for n,(q,l) in pose.items():
  pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.scale=(1,1,1)
 bpy.context.view_layer.update()
def current():return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def write(name,poses):
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 act=bpy.data.actions.new(name);act.use_fake_user=True;set_act(act);prev={}
 for f,pose in enumerate(poses):
  for n,(q,l) in pose.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':pb.location=l;pb.keyframe_insert('location',frame=f)
 act.use_frame_range=True;act.frame_start=0;act.frame_end=len(poses)-1
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 set_act(None);return act
def turn(n,axis,degrees):
 m=armik.W(rig,n);h=m.translation.copy()
 armik.set_world(rig,n,Matrix.Translation(h)@Matrix.Rotation(math.radians(degrees),4,Vector(axis))@Matrix.Translation(-h)@m)
g=json.loads((p/'work/grip_pose.json').read_text());axis=Vector(g['handle_axis_hand_local'])
fj=json.loads((p/'work/finger_joints.json').read_text())['L'];H=rig.data.bones['B_L_Hand'].matrix_local
fd=Vector(fj['B_L_Finger2'])-H.translation;ac=Vector(fj['B_L_Finger1'])-Vector(fj['B_L_Finger4'])
normal=ac.cross(fd).normalized()
if normal.y>0:normal=-normal
left_axis=H.to_3x3().inverted()@normal
left_palm=H.inverted()@(H.translation.lerp(Vector(fj['B_L_Finger2']),.65))
left_finger=H.to_3x3().inverted()@fd.normalized()
def palm_frame(normal,t):
 u=max(0,min(1,t/.20,(1.12-t)/.25));u=u*u*(3-2*u)
 finger=Vector((0,-u,-(1-u)));n=Vector(normal).normalized();finger=(finger-n*finger.dot(n)).normalized()
 local=left_finger-left_axis*left_finger.dot(left_axis);local.normalize()
 return Matrix((n,finger,n.cross(finger))).transposed()@Matrix((left_axis,local,left_axis.cross(local))).transposed().inverted()

RREADY=Vector((-.34,-.22,.98));LREADY=Vector((.40,-.05,.85));UP=Vector((-.10,-.20,.975)).normalized()
relaxed_left={}
for finger in range(5):
 for segment in range(3):
  name=f'B_L_Finger{finger}'+('' if segment==0 else str(segment));next_name=f'B_L_Finger{finger}'+str(segment+1) if segment<2 else name+'_tip'
  bone=rig.data.bones[name];direction=Vector(fj[next_name])-bone.head_local;curl=direction.cross(normal).normalized()
  local=bone.matrix_local.to_3x3().inverted()@curl;degrees=([10,15,10] if finger==0 else [20,25,15])[segment]
  relaxed_left[name]=Quaternion(local,math.radians(degrees))

def arm(side,wrist,direction,previous):
 snap={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones}
 sh=rig.pose.bones[f'B_{side}_UpperArm'].head
 length=(rig.pose.bones[f'B_{side}_Forearm'].head-sh).length+(rig.pose.bones[f'B_{side}_Hand'].head-rig.pose.bones[f'B_{side}_Forearm'].head).length
 reach=(Vector(wrist)-sh).length/length
 result=armik.solve_aimed(rig,side,wrist,axis if side=='R' else left_axis,direction,snap,prev=previous,
  phis=range(-120,121,10),k_twist=.55,twist_neutral=0,k_phi=.05,k_cont=(.15,.15,.1))
 return result,{'side':side,'frame':f,'reach':reach,'swing':result['swing'],'twist':result['twist']}
sources={n:[sample(bpy.data.actions[n],f) for f in range(int(bpy.data.actions[n].frame_range[1])+1)] for n in ['Standing','Walking','Running','CastSource']}
report={};out={}
for name in ['Standing','Walking','Running']:
 poses=[];lastR=None;lastL=None;checks=[]
 for f,pose in enumerate(sources[name]):
  apply(pose);phase=2*math.pi*f/(len(sources[name])-1)
  if name=='Standing':
   right=RREADY.copy();left=LREADY.copy();right.z+=.004*math.sin(phase);left.z+=.003*math.sin(phase)
  else:
   root_delta=rig.pose.bones['B_Pelvis'].head.z-rig.data.bones['B_Pelvis'].head_local.z
   right=RREADY+Vector((.012*math.sin(phase),.035*math.sin(phase),root_delta+.015*math.cos(phase)))
  lastR,c=arm('R',right,UP,lastR);checks.append(c)
  if name=='Standing':lastL,c=arm('L',left,Vector((-1,-.1,0)),lastL);checks.append(c)
  if name in ('Walking','Running'):turn('B_L_UpperArm',(0,-1,0),20 if name=='Running' else 10)
  if name=='Running':turn('B_Head',(1,0,0),12)
  for n,q in relaxed_left.items():rig.pose.bones[n].rotation_quaternion=q
  poses.append(current())
 # Loop endpoints are the same pose; body motion stays at the source speed.
 poses[-1]=poses[0];out[name]=poses
 report[name]={'max_reach':max(c['reach'] for c in checks),'max_wrist_swing_deg':max(c['swing'] for c in checks),'duration':(len(poses)-1)/30,'worst_wrist':max(checks,key=lambda c:c['swing']),'worst_reach':max(checks,key=lambda c:c['reach'])}
standing=out['Standing'][0]
def path(t,rows):
 ts=np.array([r[0] for r in rows]);vals=np.array([r[1] for r in rows],float)
 i=int(np.clip(np.searchsorted(ts,t)-1,0,len(ts)-2));a,b=ts[i:i+2];u=np.clip((t-a)/(b-a),0,1)
 def tangent(j):
  if j in (0,len(ts)-1):return np.zeros(vals.shape[1])
  return (vals[j+1]-vals[j-1])/(ts[j+1]-ts[j-1])
 return Vector((2*u**3-3*u**2+1)*vals[i]+(u**3-2*u**2+u)*(b-a)*tangent(i)+(-2*u**3+3*u**2)*vals[i+1]+(u**3-u**2)*(b-a)*tangent(i+1))
right_path=[(0,RREADY),(.20,(-.34,-.26,.95)),(.78,(-.35,-.27,.96)),(.86,(-.35,-.28,.99)),(1.10,(-.37,-.37,1.16)),(1.25,(-.38,-.32,1.11)),(46/30,RREADY)]
dir_path=[(0,UP),(.20,(.88,-.30,.13)),(.78,(.90,-.28,.17)),(.86,(.70,-.40,.40)),(1.10,(-.10,-.42,.90)),(1.25,(-.15,-.35,.94)),(46/30,UP)]
left_path=[(0,LREADY),(.20,(.16,-.29,1.12)),(.78,(.14,-.30,1.13)),(.86,(.26,-.32,1.07)),(1.10,(.38,-.30,1.02)),(1.25,(.42,-.22,.93)),(46/30,LREADY)]
lpalm_path=[(0,(-1,-.1,0)),(.20,(0,0,-1)),(.78,(0,0,-1)),(.86,(-.7,-.4,-.3)),(1.10,(.2,-1,.1)),(1.25,(-.6,-.5,0)),(46/30,(-1,-.1,0))]
poses=[];checks=[];lastR=lastL=None
for f in range(47):
 t=f/30;src_t=0 if t<=.86 else min(1,t-.86 if t<=1.193333 else t-.86+1/3)
 sf=src_t*30;si=min(29,int(sf));blend=sf-si
 pose={n:(q.copy(),l.copy()) for n,(q,l) in standing.items()}
 opening=max(0,min(1,t/.20,(46/30-t)/.30));opening=opening*opening*(3-2*opening)
 for n in relaxed_left:pose[n]=(pose[n][0].slerp(Quaternion(),opening),pose[n][1])
 envelope=math.sin(math.pi*min(1,t/(46/30)))**2
 for n in ['B_Spine','B_Spine1','B_Spine2','B_L_Clavicle','B_R_Clavicle']:
  sq=sources['CastSource'][si][n][0].slerp(sources['CastSource'][si+1][n][0],blend)
  pose[n]=(pose[n][0].slerp(sq,.3*envelope),pose[n][1])
 apply(pose)
 charge=max(0,math.sin(math.pi*np.clip((t-.04)/.9,0,1)))
 turn('B_Head',(1,0,0),7*charge)
 right=path(t,right_path);direction=path(t,dir_path).normalized();left=path(t,left_path)
 if .20<t<.80:
  right.z+=.008*math.sin((t-.2)/.6*4*math.pi);direction.z+=.035*math.sin((t-.2)/.6*4*math.pi)
 lastR,c=arm('R',right,direction,lastR);checks.append(c)
 guide=max(0,min(1,(t-.15)/.17,(.96-t)/.18));guide=guide*guide*(3-2*guide)
 left_normal=path(t,lpalm_path).normalized()
 lastL,c=arm('L',left,left_normal,lastL)
 wanted_hand=palm_frame(left_normal,t)
 armik.set_world(rig,'B_L_Hand',armik.rot_world(armik.W(rig,'B_L_Hand'),wanted_hand))
 if guide>0:
  target=rig.pose.bones['Socket_WandOrb'].head+Vector((.14,-.01,.18))
  for _ in range(2):
   Hpose=armik.W(rig,'B_L_Hand');error=target-Hpose@left_palm
   left=Hpose.translation+error*guide
   lastL,c=arm('L',left,left_normal,lastL)
   armik.set_world(rig,'B_L_Hand',armik.rot_world(armik.W(rig,'B_L_Hand'),wanted_hand))
 checks.append(c)
 poses.append(current())
poses[0]=standing;poses[-1]=standing;out['Attack']=poses
report['Attack']={'duration':46/30,'impact_seconds':1.10,'native_windup_seconds':1.125,'body_source':'ArmedCastRAttack1 at original speed, 0.86 s waist-charge lead; middle static source hold trimmed','max_reach':max(c['reach'] for c in checks),'max_wrist_swing_deg':max(c['swing'] for c in checks)}
report['Attack']['worst_wrist']=max(checks,key=lambda c:c['swing']);report['Attack']['worst_reach']=max(checks,key=lambda c:c['reach'])
# Select one continuous elbow/hand-roll path for the complete cast instead of changing branches per frame.
for side in ['R','L']:
 records=[];ax=axis if side=='R' else left_axis
 for f,pose in enumerate(out['Attack']):
  apply(pose);Hpose=armik.W(rig,f'B_{side}_Hand');wrist=Hpose.translation.copy();direction=Hpose.to_3x3()@ax
  for part in ['UpperArm','Forearm','Hand']:
   n=f'B_{side}_{part}';rig.pose.bones[n].rotation_quaternion=standing[n][0]
  bpy.context.view_layer.update()
  row={'snap':{pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones},'wrist':wrist,'dir':direction}
  if side=='L':
   row['hand_reference']=Hpose.to_3x3().normalized()
   from mathutils.bvhtree import BVHTree
   mesh=body.data;group_names=[g.name for g in body.vertex_groups]
   own=[sum(e.weight for e in v.groups if group_names[e.group].startswith('B_L_') and any(t in group_names[e.group] for t in ['Clavicle','UpperArm','Forearm','Hand','Finger']))>.2 for v in mesh.vertices]
   parts=[v.value for v in mesh.attributes['piece'].data]
   fl=[tuple(poly.vertices) for poly in mesh.polygons if all(parts[i] in (0,2,3,4) and not own[i] for i in poly.vertices)]
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh()
   row['clearance_tree']=BVHTree.FromPolygons([body.matrix_world@v.co for v in em.vertices],fl);ev.to_mesh_clear()
   row['forearm_vertices']=[v.index for v in mesh.vertices if sum(e.weight for e in v.groups if group_names[e.group].startswith('B_L_Forearm'))>.20]
  if f in (0,len(out['Attack'])-1):row.update(endpoint=True,hand_reference=Hpose.to_3x3().normalized())
  records.append(row)
 chosen=armik.arm_dp(rig,side,records,ax,phis=range(-120,121,10),psis=range(0,360,5),devs=(((0,0),(-20,0),(20,0),(0,-20),(0,20)) if side=='L' else ((0,0),)),k_twist=.55,twist_neutral=0,k_phi=.2,k_dphi=.8,k_dpsi=1.1,k_swing2=.03)
 ph=np.array([r['phi'] for r in chosen],float);ps=np.degrees(np.unwrap(np.radians([r['psi'] for r in chosen])))
 dv=np.array([r['dev'] for r in chosen],float)
 for values in [ph,ps,dv]:
  for _ in range(4):values[1:-1]=.25*values[:-2]+.5*values[1:-1]+.25*values[2:]
 for f,(row,opt) in enumerate(zip(records,chosen)):
  armik.apply_arm(rig,side,row['snap'],row['wrist'],ax,row['dir'],float(ph[f]),float(ps[f]),tuple(dv[f]))
  # The open palm may relax its aim after smoothing to keep its wrist within the fitted anatomical range.
  if side=='L':
   pb=rig.pose.bones['B_L_Hand'];fa=rig.data.bones['B_L_Forearm'];hd=rig.data.bones['B_L_Hand']
   physical=(hd.matrix_local.to_3x3().inverted()@(hd.head_local-fa.head_local)).normalized()
   sw,tw=armik.split_swing_twist(pb.rotation_quaternion,physical)
   if sw.w<0:sw=-sw
   sw=Quaternion().slerp(sw,min(1,math.radians(55)/max(sw.angle,1e-8)))
   pb.rotation_quaternion=sw@Quaternion(physical,max(-math.radians(82),min(math.radians(82),tw)))
   bpy.context.view_layer.update()
  out['Attack'][f]=current()
out['Attack'][0]=standing;out['Attack'][-1]=standing
checks=[]
for f,pose in enumerate(out['Attack']):
 apply(pose)
 for side in 'RL':
  sw,tw=armik.wrist_cost(rig,side,armik.W(rig,f'B_{side}_Hand').to_3x3().normalized());checks.append({'frame':f,'side':side,'swing':sw,'twist':tw})
report['Attack']['max_wrist_swing_deg']=max(r['swing'] for r in checks)
report['Attack']['worst_wrist']=max(checks,key=lambda r:r['swing'])
report['Attack']['roll_selection']='Global elbow/hand path, smoothed continuous angles, anchored ready endpoints'
for name,poses in out.items():write(name,poses)
# Existing Ogre twist distribution, with the Mage's soft wraps and fitted arm frames.
FA=.5;UA=.5;tree=ast.parse((p/'scripts/twist_bones.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist_bake','exec'),globals())
for name in out:bake_twist(bpy.data.actions[name])
set_act(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilots_authored.blend'))
(p/'review/pilot_motion.json').write_text(json.dumps(report,indent=2)+'\n');print('PILOT_MOTION',report)
common.workbench_clay(scene)
for name in out:
 set_act(bpy.data.actions[name]);n=int(bpy.data.actions[name].frame_range[1])
 for f in sorted(set([0,round(n*.25),round(n*.5),round(n*.75),n])):
  scene.frame_set(f)
  common.render_views(str(p/f'review/pilots/{name}_{f:03d}'),.9,2.2,views=('front','left','back'),resolution=(380,500))
