"""Fit finger skin to the actual irregular boulder, retaining the relaxed mesh hand."""
from pathlib import Path
import bpy,numpy as np,math,json,sys
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent));import armik
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_fitted.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data;scene=bpy.context.scene
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p/'meshy/boulder_v1/model_urls_glb.glb'));new=set(bpy.data.objects)-before
rock=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.polygons));import boulder_mesh;boulder_mesh.prepare(rock);c=np.array([v.co[:] for v in rock.data.vertices])
tree=BVHTree.FromPolygons(c.tolist(),[f.vertices[:] for f in rock.data.polygons],all_triangles=True)
for o in new:bpy.data.objects.remove(o,do_unlink=True)
co=np.array([v.co[:] for v in me.vertices]);P=np.c_[co,np.ones(len(co))]
names=[b.name for b in rig.data.bones];idx={n:i for i,n in enumerate(names)};rest=np.array([b.matrix_local for b in rig.data.bones]);inv=np.linalg.inv(rest)
parent=[idx.get(b.parent.name,-1) if b.parent else -1 for b in rig.data.bones];local=np.array([inv[parent[i]]@rest[i] if parent[i]>=0 else rest[i] for i in range(len(names))])
w=np.zeros((len(co),len(names)))
for v in me.vertices:
 for ge in v.groups:w[v.index,idx[body.vertex_groups[ge.group].name]]=ge.weight
path=json.loads((p/'work/boulder_path.json').read_text());a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
chains={};axes={};variables={};skin={}
for side in 'LR':
 hn=f'B_{side}_Hand';h=rig.data.bones[hn];kn=[rig.data.bones[f'B_{side}_Finger{i}'].head_local for i in range(5)]
 normal=(kn[1]-h.head_local).cross(kn[4]-h.head_local).normalized()*(1 if side=='R' else -1)
 for finger in range(5):
  ns=[f'B_{side}_Finger{finger}']
  while rig.data.bones[ns[-1]].children:ns.append(rig.data.bones[ns[-1]].children[0].name)
  key=(side,finger);ch=[idx[n] for n in ns];chains[key]=ch
  direction=(rig.data.bones[ns[1]].head_local-rig.data.bones[ns[0]].head_local).normalized();hinge=direction.cross(normal).normalized()
  axes[key]=[np.array(rest[j,:3,:3].T)@np.array(hinge) for j in ch]
  variables[key]=np.zeros(5)
  ids=np.flatnonzero(w[:,ch].sum(1)>.30);assert len(ids)>5,(key,len(ids));skin[key]=ids
  axes[key].append(np.array(rest[ch[0],:3,:3].T)@np.array(normal))
  axes[key].append(np.array(rest[ch[0],:3,:3].T)@np.array(direction))
def rotation(axis,degrees):return np.array(Quaternion(Vector(axis),math.radians(float(degrees))).to_matrix())
def matrices(key,angles,base):
 ch=chains[key];out=base.copy()
 for k,j in enumerate(ch):
  q=rotation(axes[key][k],angles[k])
  if k==0:q=rotation(axes[key][3],angles[3])@rotation(axes[key][4],angles[4])@q
  m=np.eye(4);m[:3,:3]=q;out[j]=out[parent[j]]@local[j]@m
 return out
rock_lo,rock_hi=c.min(0),c.max(0)
ray_direction=Vector((1,.371,.223)).normalized()
def signed(points):
 result=[]
 for point in points:
  v=Vector(point);hit,normal,face,d=tree.find_nearest(v)
  inside=False
  if np.all(point>=rock_lo) and np.all(point<=rock_hi):
   origin=v.copy();count=0
   for _ in range(32):
    hit,n,index,distance=tree.ray_cast(origin,ray_direction)
    if hit is None:break
    count+=1;origin=hit+ray_direction*.000001
   else:raise AssertionError('boulder ray did not escape')
   inside=bool(count%2)
  result.append(-d if inside else d)
 return np.array(result)
assert (signed(np.array([[x,y,z] for x in [-.4,.4] for y in [-.25,.25] for z in [-.24,.24]]))>0).all()
def evaluate(key,angles,base,centre):
 mats=matrices(key,angles,base);ids=skin[key];trans=mats@inv
 posed=np.einsum('vj,jab,vb->va',w[ids],trans,P[ids])[:,:3]-centre
 d=signed(posed);gap=max(d.min(),0);penetration=np.minimum(d,0)
 # Every finger makes skin contact; no finger is allowed to burrow through the stone.
 cost=.00000003*np.sum((angles-variables[key])**2)+800*gap*gap+6000*np.mean(penetration**2)+2000*min(d.min(),0)**2+.000000001*np.sum(angles**2)
 return cost, d, mats
fitted={};report=[];arm_deltas={};palm_reports=[];palm_angles={}
arm_names=[f'B_{side}_{part}' for side in 'LR' for part in ['UpperArm','Forearm','Hand']]
for f in range(9,30):
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(f)
 snapshot={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones};rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis=snapshot[pb.name]
 bpy.context.view_layer.update();centre=np.array(path[f]['centre']);qframe={}
 # Place the palm skin against the stone before fitting individual fingers.
 for side,sign in [('L',1),('R',-1)]:
  hn=f'B_{side}_Hand';hand_ids=np.flatnonzero(w[:,idx[hn]]>.55)
  knuckles=np.mean([rest[idx[f'B_{side}_Finger{i}'],:3,3] for i in range(1,5)],axis=0);forward=knuckles-rest[idx[hn],:3,3]
  along=(co[hand_ids]-rest[idx[hn],:3,3])@forward/(forward@forward)
  hand_ids=hand_ids[(along>.2)&(along<.95)]
  assert len(hand_ids)>8,(side,len(hand_ids))
  base=np.array([pb.matrix for pb in rig.pose.bones]);posed=np.einsum('vj,jab,vb->va',w,base@inv,P)[:,:3]-centre
  M=armik.W(rig,hn);pivot=np.mean(posed[hand_ids],axis=0);world_forward=M.to_3x3()@Vector(inv[idx[hn],:3,:3]@forward);world_forward.normalize()
  width=rig.pose.bones[f'B_{side}_Finger1'].matrix.translation-rig.pose.bones[f'B_{side}_Finger4'].matrix.translation;width.normalize()
  axis=np.array([sign*.94,0.,-.34]);best=None;old=palm_angles.get(side,np.zeros(2))
  for roll in np.arange(-40,41,10):
   for pitch in np.arange(-30,31,10):
    R=np.array((Quaternion(width,math.radians(float(pitch)))@Quaternion(world_forward,math.radians(float(roll)))).to_matrix())
    points=(posed[hand_ids]-pivot)@R.T+pivot;lo,hi=-.15,.15
    for _ in range(11):
     mid=(lo+hi)/2
     if signed(points+mid*axis).min()<.001:lo=mid
     else:hi=mid
    shift=(lo+hi)/2;score=0.
    for fi in range(5):
     points=(posed[skin[side,fi]]-pivot)@R.T+pivot+shift*axis;d=signed(points)
     score+=5*max(d.min(),0)**2+10*np.mean(np.minimum(d,0)**2)
    values=np.array([roll,pitch]);score+=.00000005*np.sum(values**2)+.0000002*np.sum((values-old)**2)
    if best is None or score<best[0]:best=(score,R,shift,values)
  _,R,shift,values=best;palm_angles[side]=values
  target=Vector(R@(np.array(M.translation)-centre-pivot)+pivot+centre+axis*shift)
  pole=armik.W(rig,f'B_{side}_Forearm').translation.copy();armik.solve(rig,side,target,pole=pole,hand_rot=Matrix(R.tolist())@M.to_3x3())
  for iteration in range(3):
   base=np.array([pb.matrix for pb in rig.pose.bones]);points=np.einsum('vj,jab,vb->va',w[hand_ids],base@inv,P[hand_ids])[:,:3]-centre
   axis=np.array([sign*.94,0.,-.34]);lo,hi=-.09,.09
   assert signed(points+hi*axis).min()>0,'palm cannot clear stone'
   for _ in range(12):
    mid=(lo+hi)/2
    if signed(points+mid*axis).min()<.001:lo=mid
    else:hi=mid
   shift=(lo+hi)/2;M=armik.W(rig,hn);pole=armik.W(rig,f'B_{side}_Forearm').translation.copy()
   reach=armik.solve(rig,side,M.translation+Vector(axis*shift),pole=pole,hand_rot=M.to_3x3())
   assert reach<1.04,('palm reach',f,side,reach)
  base=np.array([pb.matrix for pb in rig.pose.bones]);points=np.einsum('vj,jab,vb->va',w[hand_ids],base@inv,P[hand_ids])[:,:3]-centre
  palm_reports.append({'frame':f,'side':side,'distance_mm':float(signed(points).min()*1000)})
 arm_deltas[f]={n:snapshot[n].to_quaternion().inverted()@rig.pose.bones[n].rotation_quaternion for n in arm_names}
 base=np.array([rig.pose.bones[n].matrix for n in names])
 if f==9:
  calculated=np.einsum('vj,jab,vb->va',w,base@inv,P)[:,:3]
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());evaluated=ev.to_mesh();actual=np.array([v.co[:] for v in evaluated.vertices]);ev.to_mesh_clear()
  assert np.max(np.linalg.norm(actual-calculated,axis=1))<.00002,'skin evaluator differs from Blender'
 for key in chains:
  solutions=[]
  seeds=[variables[key].copy(),np.zeros(5)]
  initial=evaluate(key,seeds[0],base,centre)[1]
  if initial.min()<-.002 or initial.min()>.002:
   seeds += [np.array([a,0.,0.,b,c]) for a in [-40.,40.] for b in [-45.,45.] for c in [-50.,50.]]
  for seed in seeds:
   angles=seed.copy()
   for step in [20,8,3,1]:
    for sweep in range(2):
     for k in range(5):
      trials=[]
      for delta in [-step,0,step]:
       candidate=angles.copy();candidate[k]=np.clip(candidate[k]+delta,-75,90) if k<3 else np.clip(candidate[k]+delta,-100 if key[1]==0 else -70,100 if key[1]==0 else 70)
       trials.append((evaluate(key,candidate,base,centre)[0],candidate))
      angles=min(trials,key=lambda row:row[0])[1]
   solutions.append((evaluate(key,angles,base,centre)[0],angles.copy()))
  angles=min(solutions,key=lambda v:v[0])[1]
  cost,d,mats=evaluate(key,angles,base,centre);variables[key]=angles;base=mats
  for j in chains[key]:qframe[names[j]]=Matrix((np.linalg.inv(local[j])@np.linalg.inv(mats[parent[j]])@mats[j]).tolist()).to_quaternion()
  report.append({'frame':f,'hand':key[0],'finger':key[1],'gap_mm':float(max(d.min(),0)*1000),'penetration_mm':float(max(-d.min(),0)*1000),'angles':angles.tolist()})
 fitted[f]=qframe
 print('FINGER_CONTACT',f,'gap',round(max(r['gap_mm'] for r in report if r['frame']==f),2),'penetration',round(max(r['penetration_mm'] for r in report if r['frame']==f),2),flush=True)
rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
# Ease into the pickup grip and open the fingers after release.
for f in range(49):
 scene.frame_set(f)
 for n in arm_names:
  delta=arm_deltas[min(29,max(9,f))][n]
  gain=min(1,f/9) if f<9 else max(0,1-(f-29)/7) if f>29 else 1
  pb=rig.pose.bones[n];pb.rotation_quaternion=pb.rotation_quaternion@Quaternion().slerp(delta,gain);pb.keyframe_insert('rotation_quaternion',frame=f)
 if f<9:pose={n:Quaternion().slerp(q,(f/9)**2*(3-2*f/9)) for n,q in fitted[9].items()}
 elif f<=29:pose=fitted[f]
 else:pose={n:q.slerp(Quaternion(),min(1,(f-29)/7)) for n,q in fitted[29].items()}
 for n,q in pose.items():
  pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    if 'Finger' in fc.data_path:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
(p/'work/palm_contact.json').write_text(json.dumps(palm_reports,indent=2))
(p/'work/grip_contact.json').write_text(json.dumps(report,indent=2))
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_fitted.blend'))
