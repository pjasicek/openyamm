"""Fold the long hull panels at their strap hinges during the grounded fall."""
import bpy,sys,os,json,math
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/forge_apron_surface_checkpoint.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;body=bpy.data.objects['Body']
parts=[bpy.data.objects[f'Apron_{side}{k}'] for side in ('Front','Back') for k in (1,2)];names=[o.vertex_groups[0].name for o in parts]
fixed=[o for o in bpy.data.objects if o.type=='MESH' and (o.name=='Body' or o.name.startswith('Arm_') or o.name in ('Apron_Front0','Apron_Strap_L','Apron_Strap_R'))]
BF=[tuple(f.vertices) for f in body.data.polygons];DIRS=[Vector(v).normalized() for v in ((.0123,.0217,1),(.71,-.33,-.62),(-.55,.81,.2))]
def coords(ob):
 e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();v=np.array([list(ob.matrix_world@p.co) for p in me.vertices]);e.to_mesh_clear();return v

def inside(tree,p):
 votes=0
 for d in DIRS:
  q=Vector(p);num=0;travel=0.
  while travel<4:
   hit,_,_,dist=tree.ray_cast(q,d,4-travel)
   if hit is None:break
   num+=1;travel+=dist+1e-5;q=hit+d*1e-5
  votes+=num%2
 return votes>=2
local={};sample={}
for ob,bn in zip(parts,names):
 inv=r.data.bones[bn].matrix_local.inverted();V=np.array([list(inv@v.co) for v in ob.data.vertices]);local[bn]=V
 faces=[list(p.vertices) for p in ob.data.polygons if p.material_index==0];points=np.vstack([V,*[V[f].mean(0)[None,:] for f in faces]])
 sample[bn]=np.unique(np.round(points,5),axis=0)

def surface(M,V):return V@np.array(M.to_3x3()).T+np.array(M.translation)
def measure(V,tree):
 floor=max(0,.006-float(V[:,2].min()));depth=0
 for p in V:
  loc,n,fi,d=tree.find_nearest(Vector(p),.20)
  if loc is not None and d>depth and (Vector(p)-loc).dot(n)<-1e-4 and inside(tree,p):depth=d
 return depth,floor

def project(V,tree):
 D=np.zeros(3)
 for _ in range(12):
  largest=0.
  for v in V:
   p=v+D;delta=np.array([0.,0.,max(0,.007-p[2])]);p+=delta;loc,n,fi,d=tree.find_nearest(Vector(p),.15)
   if loc is not None and ((d>.0001 and (Vector(p)-loc).dot(n)<-1e-4 and inside(tree,p)) or d<.006):delta+=np.array(loc+n*.008)-p
   D+=delta;largest=max(largest,float(np.linalg.norm(delta)))
   if np.linalg.norm(D)>.10:return None
  if largest<.0005:break
 return D

a=bpy.data.actions['Forge_Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];frames=np.arange(a.frame_range[0],a.frame_range[1]+.001,.5);keys=[];previous={};report=[]
for f in frames:
 sc.frame_set(int(f),subframe=float(f%1));maul=armik.W(r,'Thunder_Maul').copy()
 for bn in names:r.pose.bones[bn].matrix_basis.identity()
 bpy.context.view_layer.update();lift=max(0,.008-min(coords(o)[:,2].min() for o in fixed));root=armik.W(r,'B_Pelvis');root.translation.z+=float(lift);armik.set_world(r,'B_Pelvis',root);armik.set_world(r,'Thunder_Maul',maul)
 tree=BVHTree.FromPolygons(coords(body).tolist(),BF);row={'frame':float(f),'root_lift_m':float(lift),'panels':{}}
 for ob,bn in zip(parts,names):
  # The strap's root follows the preceding panel; only the hinge angle and a small surface correction can change.
  r.pose.bones[bn].matrix_basis.identity();bpy.context.view_layer.update();base=armik.W(r,bn);rank=[]
  for deg in range(-180,180,10):
   m=base@Matrix.Rotation(math.radians(deg),4,'X');V=surface(m,sample[bn]);dep,floor=measure(V,tree)
   q=m.to_quaternion();change=0 if bn not in previous else min(q.rotation_difference(previous[bn]).angle,2*math.pi-q.rotation_difference(previous[bn]).angle)
   rank.append((1e5*(dep+floor)+.05*change*change+.005*float(V[:,2].mean()),deg,m,change))
  best=None
  for _,deg,coarse,change in sorted(rank,key=lambda x:x[0])[:5]:
   for fine in (-4,-2,0,2,4):
    m=base@Matrix.Rotation(math.radians(deg+fine),4,'X');V=surface(m,sample[bn]);D=project(V,tree)
    if D is None:continue
    m.translation+=Vector(D);dep,floor=measure(surface(m,sample[bn]),tree);q=m.to_quaternion();change=0 if bn not in previous else min(q.rotation_difference(previous[bn]).angle,2*math.pi-q.rotation_difference(previous[bn]).angle)
    cost=1e6*(dep+floor)+.04*change*change+3*float(D@D)+.01*float(surface(m,local[bn])[:,2].mean())
    if best is None or cost<best[0]:best=(cost,m,deg+fine,D,dep,floor)
  assert best is not None,(float(f),bn,'no hinge solution')
  _,m,angle,D,dep,floor=best;assert dep<=.003 and floor<=.003,(float(f),bn,dep,floor)
  armik.set_world(r,bn,m);previous[bn]=m.to_quaternion();row['panels'][bn]={'angle':angle,'correction_m':float(np.linalg.norm(D)),'penetration_m':dep,'floor_error_m':floor}
 keys.append((float(f),{n:r.pose.bones[n].matrix_basis.copy() for n in [*names,'B_Pelvis','Thunder_Maul']}));report.append(row)
 if int(f*2)%20==0:print('FALL_HINGES',f,'lift',round(float(lift),3),{n:x['angle'] for n,x in row['panels'].items()},flush=True)
previous={}
for f,pose in keys:
 for n,m in pose.items():
  b=r.pose.bones[n];q=m.to_quaternion()
  if n in previous and q.dot(previous[n])<0:q=-q
  previous[n]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    if any(n in fc.data_path for n in [*names,'B_Pelvis','Thunder_Maul']):
     for key in fc.keyframe_points:key.interpolation='LINEAR'
# Hold the complete corrected fall, with the released weapon staying in world space.
sc.frame_set(int(a.frame_range[1]));end={b.name:b.matrix_basis.copy() for b in r.pose.bones if b.name.startswith('B_ForgeApron_') or b.name=='B_Pelvis'};weapon=armik.W(r,'Thunder_Maul').copy();dead=bpy.data.actions['Forge_Dead'];r.animation_data.action=dead;r.animation_data.action_slot=dead.slots[0]
for f in (0,float(dead.frame_range[1])):
 sc.frame_set(int(f))
 for n,m in end.items():r.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update();armik.set_world(r,'Thunder_Maul',weapon)
 for n in [*end,'Thunder_Maul']:
  b=r.pose.bones[n];b.rotation_mode='QUATERNION';b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_concept_fit.blend'));(P/'review/forge_death_hinges.json').write_text(json.dumps(report,indent=2)+'\n');sys.stdout.flush();os._exit(0)
