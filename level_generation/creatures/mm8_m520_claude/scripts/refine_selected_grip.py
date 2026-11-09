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
# Fit the complete triangle surface at one pose, then carry this fixed grip through the throw.
f=12;rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(f);snapshot={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones};rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=snapshot[pb.name]
bpy.context.view_layer.update();centre=np.array(path[24]['centre']);faces=np.array([poly.vertices[:] for poly in me.polygons]);bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3]);surface={};palm={}
for side in 'LR':
 channels=[j for j,n in enumerate(names) if n==f'B_{side}_Hand' or n.startswith(f'B_{side}_Finger')];eligible=w[:,channels].sum(1)>.3;tris=faces[eligible[faces].all(1)];ids=np.unique(tris);mapping=np.full(len(co),-1);mapping[ids]=np.arange(len(ids));localtris=mapping[tris]
 for fi in range(5):
  mask=np.einsum('sk,tk->ts',bary,w[:,chains[side,fi]].sum(1)[tris]).ravel()>.3;surface[side,fi]=(ids,localtris,mask)
 mask=np.einsum('sk,tk->ts',bary,w[:,idx[f'B_{side}_Hand']][tris]).ravel()>.3;palm[side]=(ids,localtris,mask)
def surface_points(spec,base):
 ids,tris,mask=spec;posed=np.einsum('vj,jab,vb->va',w[ids],base@inv,P[ids])[:,:3]-centre
 return np.einsum('sk,tkj->tsj',bary,posed[tris]).reshape(-1,3)[mask]
for side,sign in [('L',1),('R',-1)]:
 for _ in range(3):
  base=np.array([rig.pose.bones[n].matrix for n in names]);points=surface_points(palm[side],base);axis=np.array([sign*.94,0.,-.34]);lo,hi=-.10,.10
  assert signed(points+hi*axis).min()>0
  for _ in range(14):
   mid=(lo+hi)/2
   if signed(points+mid*axis).min()<.001:lo=mid
   else:hi=mid
  H=armik.W(rig,f'B_{side}_Hand');pole=armik.W(rig,f'B_{side}_Forearm').translation.copy();armik.solve(rig,side,H.translation+Vector(axis*(lo+hi)/2),pole=pole,hand_rot=H.to_3x3())
base=np.array([rig.pose.bones[n].matrix for n in names]);previous=json.loads((p/'work/grip_contact.json').read_text())
for key in chains:variables[key]=np.array(next(row['angles'] for row in previous if row['frame']==12 and row['hand']==key[0] and row['finger']==key[1]))
def evaluate(key,angles,base,centre):
 mats=matrices(key,angles,base);d=signed(surface_points(surface[key],mats));gap=max(d.min(),0);depth=np.minimum(d,0)
 cost=800*gap*gap+6000*np.mean(depth**2)+2000*min(d.min(),0)**2+.00000003*np.sum((angles-variables[key])**2)
 return cost,d,mats
for sweep in range(3):
 for key in chains:
  angles=variables[key].copy();seeds=[angles,np.zeros(5)] if sweep==0 else [angles]
  if evaluate(key,angles,base,centre)[1].min()<-.003:seeds += [np.array([v,0,0,0,r]) for v in [-40,40] for r in [-50,50]]
  solutions=[]
  for seed in seeds:
   angles=seed.copy()
   for step in [16,6,2,.5]:
    for _ in range(3):
     for k in range(5):
      trials=[]
      for delta in [-step,0,step]:
       candidate=angles.copy();candidate[k]=np.clip(candidate[k]+delta,-75 if k<3 else -100,90 if k<3 else 100);trials.append((evaluate(key,candidate,base,centre)[0],candidate))
      angles=min(trials,key=lambda row:row[0])[1]
   solutions.append((evaluate(key,angles,base,centre)[0],angles.copy()))
  angles=min(solutions,key=lambda row:row[0])[1];variables[key]=angles;_,d,base=evaluate(key,angles,base,centre)
  print('GRIP_SURFACE',sweep,key,'gap',max(d.min(),0)*1000,'depth',max(-d.min(),0)*1000,flush=True)
report=[]
for key in chains:
 _,d,mats=evaluate(key,variables[key],base,centre);report.append({'hand':key[0],'finger':key[1],'gap_mm':float(max(d.min(),0)*1000),'penetration_mm':float(max(-d.min(),0)*1000),'angles':variables[key].tolist()})
 for j in chains[key]:rig.pose.bones[names[j]].rotation_quaternion=Matrix((np.linalg.inv(local[j])@np.linalg.inv(mats[parent[j]])@mats[j]).tolist()).to_quaternion()
bpy.context.view_layer.update();r={'source':'working_07 full surface grip fit at 0.4 seconds','frame':12,'centre':centre.tolist(),'hands':{}}
for side in 'LR':r['hands'][side]={'matrix':[list(row) for row in rig.pose.bones[f'B_{side}_Hand'].matrix],'fingers':{pb.name:list(pb.rotation_quaternion) for pb in rig.pose.bones if pb.name.startswith(f'B_{side}_Finger')}}
(p/'work/grip_surface_report.json').write_text(json.dumps(report,indent=2));(p/'work/grip_surface_candidate.json').write_text(json.dumps(r,indent=2))
assert max(max(row['gap_mm'],row['penetration_mm']) for row in report)<2.5,'grip surface still needs fitting'
(p/'work/selected_grip.json').write_text(json.dumps(r,indent=2));print('SELECTED_SURFACE_GRIP',flush=True)
