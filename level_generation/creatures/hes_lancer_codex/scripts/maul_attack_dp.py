"""Fit a continuous two-hand path to the stored attack's actual weapon trajectory."""
import json,math,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix,Quaternion,Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/forge_raw.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene
G={s:json.loads((P/f'work/grip_pose_{"R" if s=="R" else "L_tun"}.json').read_text()) for s in 'LR'}
C={s:Vector(G[s]['handle_centre_hand_local']) for s in 'LR'}
A={s:Vector(G[s]['handle_axis_hand_local']).normalized() for s in 'LR'}
S=Vector(json.loads((P/'work/maul_source_grips.json').read_text())['R']['axis_hand']).normalized()
def sample(act,f):
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];scene.frame_set(f)
 return {b.name:b.matrix_basis.copy() for b in rig.pose.bones}
source=bpy.data.actions['Forge_Attack'];duration=int(source.frame_range[1]);targets=[];headings=[];forward_local=None
for f in range(duration+1):
 sample(source,f);h=armik.W(rig,'B_R_Hand');targets.append((h@C['R'],(h.to_3x3().normalized()@S).normalized()))
 chest_rotation=armik.W(rig,'B_Spine2').to_3x3().normalized()
 if forward_local is None:forward_local=chest_rotation.inverted()@Vector((0,-1,0))
 forward=chest_rotation@forward_local;headings.append(math.atan2(forward.x,-forward.y))
headings=np.clip(.85*np.unwrap(headings),-math.radians(80),math.radians(80));print('SOURCE_TORSO_YAW',np.degrees(headings).tolist(),flush=True)
base=sample(bpy.data.actions['Carbine_Standing'],0);rig.animation_data.action=None
spine=armik.W(rig,'B_Spine').copy();turns=[]
for yaw in headings:
 rot=Quaternion((0,0,1),float(yaw));t=rot.to_matrix().to_4x4();t.translation=spine.translation-rot@spine.translation;turns.append(t)
for side in 'LR':
 for n,q in G[side]['finger_local'].items():rig.pose.bones[n].rotation_quaternion=Quaternion(q);base[n]=rig.pose.bones[n].matrix_basis.copy()
bpy.context.view_layer.update()
reference={s:[armik.W(rig,f'B_{s}_{n}').copy() for n in ('UpperArm','Forearm','Hand')] for s in 'LR'}
rest={s:(rig.data.bones[f'B_{s}_Forearm'].matrix_local.to_3x3().inverted()@rig.data.bones[f'B_{s}_Hand'].matrix_local.to_3x3()).inverted() for s in 'LR'}
wa={s:(rig.data.bones[f'B_{s}_Hand'].matrix_local.to_3x3().inverted()@(rig.data.bones[f'B_{s}_Hand'].head_local-rig.data.bones[f'B_{s}_Forearm'].head_local)).normalized() for s in 'LR'}
body=bpy.data.objects['Body'];names=[g.name for g in body.vertex_groups]
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
handpoints={s:np.unique(np.array([reference[s][2].inverted()@(body.matrix_world@mesh.vertices[v.index].co) for v in body.data.vertices if sum(e.weight for e in v.groups if names[e.group].startswith(f'B_{s}_') and any(t in names[e.group] for t in ('Hand','Finger')))>.25]),axis=0) for s in 'LR'}
ev.to_mesh_clear()
chest=np.array((0,-.12,1.36));chest_radius=np.array((.24,.24,.28))
def candidates(side,centre,axis,other=None):
 u,f,h=reference[side];sh,el,wr=u.translation,f.translation,h.translation
 l1,l2=(el-sh).length,(wr-el).length
 out=[]; stats=[0,0,0,180.]
 for psi in range(0,360,15):
  R=armik.hand_rot(A[side],axis,psi);target=centre-R@C[side];d=target-sh;dist=d.length
  if dist> .98*(l1+l2) or dist<abs(l1-l2)+.01:continue
  stats[0]+=1
  direction=d.normalized();normal=(el-sh)-direction*(el-sh).dot(direction)
  if normal.length<1e-5:normal=direction.orthogonal()
  normal.normalize();ca=max(-1,min(1,(l1*l1+dist*dist-l2*l2)/(2*l1*dist)))
  hp=handpoints[side]@np.array(R).T+np.array(target)
  if np.min(np.linalg.norm((hp-chest)/chest_radius,axis=1))<1.04:continue
  stats[1]+=1
  for phi in range(-180,180,20):
   e=sh+l1*(direction*ca+(Quaternion(direction,math.radians(phi))@normal)*math.sqrt(1-ca*ca))
   a0,a1=(el-sh).normalized(),(e-sh).normalized();q=a0.rotation_difference(a1)
   n0,n1=(el-sh).cross(wr-el),(e-sh).cross(target-e)
   if n0.length>1e-6 and n1.length>1e-6:
    n0=q@n0;n0=(n0-a1*n0.dot(a1)).normalized();n1=(n1-a1*n1.dot(a1)).normalized()
    q=Quaternion(a1,math.atan2(a1.dot(n0.cross(n1)),n0.dot(n1)))@q
   ru=q.to_matrix()@u.to_3x3().normalized();rf=q.to_matrix()@f.to_3x3().normalized()
   qf=(q@(wr-el)).normalized().rotation_difference((target-e).normalized());rf=qf.to_matrix()@rf
   rel=rest[side]@(rf.inverted()@R);sw,tw=armik.split_swing_twist(rel.to_quaternion(),wa[side])
   swing=math.degrees(min(sw.angle,2*math.pi-sw.angle));twist=math.degrees(tw)
   stats[3]=min(stats[3],swing)
   if swing>54 or abs(twist)>165:continue
   stats[2]+=1
   # Closed skin clearance is checked again on the fully skinned mesh after this geometric search.
   if any(np.linalg.norm((np.array(point)-chest)/chest_radius)<1.03 for point in (e,e.lerp(target,.5))):continue
   if other is not None:
    blocked=False
    for start,end,radius in ((sh,e,.085),(e,target,.085)):
     av,bv=np.array(start),np.array(end);seg=bv-av;t=np.clip((other-av)@seg/seg.dot(seg),0,1)
     if np.linalg.norm(other-av-t[:,None]*seg,axis=1).min()<radius+.012:blocked=True;break
    if blocked:continue
   mats=[]
   for rot,point in ((ru,sh),(rf,e),(R,target)):
    m=rot.to_4x4();m.translation=point;mats.append(m)
   cost=swing+.12*abs(twist)+.02*abs(phi)
   out.append(dict(cost=cost,mats=mats,twist=twist,points=hp,psi=psi,phi=phi,swing=swing,centre=centre.copy()))
 if side=='R' and not out:print('EMPTY_RIGHT',list(centre),stats,flush=True)
 return out

def diverse(items,count):
 groups={}
 for x in sorted(items,key=lambda x:x['cost']):
  key=(int((x['twist']+180)//45),x['phi']//60)
  if key not in groups:groups[key]=x
 result=list(groups.values())[:count]
 if len(result)<count:
  used={id(x) for x in result};result.extend(x for x in sorted(items,key=lambda x:x['cost']) if id(x) not in used)
 return result[:count]

frames=[]
for f,(rawcentre,world_axis) in enumerate(targets):
 axis=turns[f].to_3x3().inverted()@world_axis
 rawcentre=turns[f].inverted()@rawcentre
 centre=rawcentre.copy();centre.y=-.50;centre.z=max(1.0,min(1.65,centre.z),1.4+.5*axis.y-.4*max(0,axis.z));centre.x=-.2*axis.x-.15*max(0,-axis.y)
 rights=[]
 for offset in ((0,0,0),(0,.12,0),(0,0,-.12),(0,.12,-.12),(0,0,.12),(0,-.12,0),(.12,0,0),(-.12,0,0),(0,0,.24)):
  for c in diverse(candidates('R',centre+Vector(offset),axis),6):c['cost']+=120*np.linalg.norm(offset);rights.append(c)
 choices=[]
 for r in rights:
  for spacing in (.30,.42,.54):
   for l in diverse(candidates('L',r['centre']+axis*spacing,-axis,r['points'])+candidates('L',r['centre']+axis*spacing,axis,r['points']),3):
    q=np.array([(turns[f]@m).to_quaternion()[:] for c in (r,l) for m in c['mats']])
    choices.append(dict(R=r,L=l,cost=r['cost']+l['cost'],q=q,tw=np.array([r['twist'],l['twist']]),spacing=spacing))
 assert choices,('No valid two-hand pose',f, len(rights),list(centre),list(axis))
 choices=sorted(choices,key=lambda x:x['cost'])[:90]
 frames.append(choices)
 print('DP_FRAME',f,len(rights),len(choices),round(choices[0]['cost'],1),flush=True)

cost=np.array([c['cost'] for c in frames[0]]);backs=[]
for i,choices in enumerate(frames[1:],1):
 qa=np.array([c['q'] for c in frames[i-1]]);qb=np.array([c['q'] for c in choices])
 angles=np.degrees(2*np.arccos(np.clip(np.abs(np.einsum('ajk,bjk->abj',qa,qb)),0,1)))
 tw=np.abs(np.array([c['tw'] for c in frames[i-1]])[:,None,:]-np.array([c['tw'] for c in choices])[None,:,:])
 transition=.06*np.sum(angles**2,axis=2)
 transition[(tw.max(2)>80)|(angles.max(2)>85)]=1e12
 table=cost[:,None]+transition;back=table.argmin(0);cost=table[back,np.arange(len(choices))]+np.array([c['cost'] for c in choices]);backs.append(back)
assert cost.min()<1e11,('No continuous anatomical path',float(cost.min()))
index=int(cost.argmin());path=[index]
for b in reversed(backs):index=int(b[index]);path.append(index)
path.reverse()
bpy.data.actions.remove(bpy.data.actions['Forge_Attack']);act=bpy.data.actions.new('Forge_Attack');act.use_fake_user=True
rig.animation_data.action=act;previous={};report=[];trajectory=[]
for f,index in enumerate(path):
 choice=frames[f][index]
 for n,m in base.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
 armik.set_world(rig,'B_Spine',turns[f]@spine)
 for side in 'RL':
  for name,m in zip(('UpperArm','Forearm','Hand'),choice[side]['mats']):armik.set_world(rig,f'B_{side}_{name}',turns[f]@m)
 for b in rig.pose.bones:
  b.rotation_mode='QUATERNION';q=b.matrix_basis.to_quaternion()
  if b.name in previous and q.dot(previous[b.name])<0:q=-q
  previous[b.name]=q.copy();b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
 errors={side:(armik.W(rig,f'B_{side}_Hand')@C[side]-(turns[f]@choice['R']['centre']+(targets[f][1]*choice['spacing'] if side=='L' else Vector()))).length for side in 'RL'}
 assert max(errors.values())<.001,errors
 report.append(dict(frame=f,left_wrist=choice['L']['swing'],right_wrist=choice['R']['swing'],left_twist=choice['L']['twist'],right_twist=choice['R']['twist'],spacing=choice['spacing'],grip_errors=errors))
 z=Vector((0,1,0));z=(z-A['R']*z.dot(A['R'])).normalized();point=C['R']+A['R']*1.02+A['R'].cross(z).normalized()*.335
 impact=armik.W(rig,'B_R_Hand')@point;trajectory.append(dict(time=f/30,impact_socket_y_up=[impact.x,impact.z,-impact.y]))
act.use_frame_range=True;act.frame_start=0;act.frame_end=duration
rig.animation_data.action=None
(P/'review/maul_attack_dp.json').write_text(json.dumps(report,indent=2)+'\n')
(P/'review/maul_strike_trajectory.json').write_text(json.dumps(trajectory,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_motion.blend'))
