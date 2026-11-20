"""Fit the actual broad rigid hull panels after the Harrower strip simulation."""
import bpy,sys,os,json,math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
death_only=False
bpy.ops.wm.open_mainfile(filepath=str(P/('work/forge_apron_surface_checkpoint.blend' if death_only else 'work/forge_apron_sim.blend')));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
cloth=[bpy.data.objects[f'Apron_{side}{k}'] for side in ('Front','Back') for k in range(3) if f'Apron_{side}{k}' in bpy.data.objects]
BF=[tuple(f.vertices) for f in body.data.polygons];DIRS=[Vector(v).normalized() for v in ((.0123,.0217,1),(.71,-.33,-.62),(-.55,.81,.2),(.12,-.97,.21),(-.83,-.18,-.52))]
def coords(ob):
 e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=np.array([list(ob.matrix_world@p.co) for p in m.vertices]);e.to_mesh_clear();return v

def inside(tree,p):
 votes=0
 for d in DIRS:
  q=Vector(p);count=0;travel=0.
  while travel<4:
   hit,_,_,dist=tree.ray_cast(q,d,4-travel)
   if hit is None:break
   count+=1;travel+=dist+1e-5;q=hit+d*1e-5
  votes+=count%2
 return votes>=3

def project(V,tree,D,floor=True):
 for _ in range(25):
  biggest=0
  for v in V:
   p=v+D;delta=np.array([0.,0.,max(0,.008-p[2]) if floor else 0.]);p+=delta
   loc,n,fi,dist=tree.find_nearest(Vector(p),.20)
   if loc is not None and ((dist>.0001 and (Vector(p)-loc).dot(n)<-.4*dist and inside(tree,p)) or dist<.010):delta+=np.array(loc+n*.014)-p
   D+=delta;biggest=max(biggest,float(np.linalg.norm(delta)))
  if biggest<.0005:break
 return D
report={}
for a in [bpy.data.actions['Forge_'+x] for x in (('Death',) if death_only else ('Standing','Walking','Running','Attack','Hit','Fidget','Cast'))]:
 r.animation_data.action=None
 for b in r.pose.bones:
  if b.name.startswith('B_ForgeApron_'):b.matrix_basis.identity()
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];cache=[];corr={o.name:[] for o in cloth};frames=np.arange(a.frame_range[0],a.frame_range[1]+.001,.5)
 for f in frames:
  sc.frame_set(int(f),subframe=float(f%1))
  if death_only:
   for ob in cloth:
    b=r.pose.bones[ob.vertex_groups[0].name];b.matrix_basis.identity()
   bpy.context.view_layer.update()
  V=coords(body);faces=list(BF);verts=list(V)
  # Existing hull plates are solid obstacles as well as the visible Kreegan body.
  for ob in [o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Arm_')]:
   off=len(verts);verts.extend(coords(ob));faces.extend(tuple(off+i for i in p.vertices) for p in ob.data.polygons if p.material_index==0)
  tree=BVHTree.FromPolygons([tuple(v) for v in verts],faces);row={}
  for ob in cloth:
   v=coords(ob);bn=ob.vertex_groups[0].name;m=armik.W(r,bn).copy();d=project(v,tree,np.zeros(3),ob['chain_index']>0 and not death_only);corr[ob.name].append(d);row[ob.name]=(v,m)
  cache.append((tree,row))
 for name,ds in corr.items():
  ds=np.array(ds);weights=np.exp(-.5*(np.arange(-3,4)/1.3)**2);weights/=weights.sum();ix=np.clip(np.arange(len(ds))[:,None]+np.arange(-3,4),0,len(ds)-1);corr[name]=(ds[ix]*weights[None,:,None]).sum(1)
 keys=[];mx=0.
 for i,(f,(tree,row)) in enumerate(zip(frames,cache)):
  sc.frame_set(int(f),subframe=float(f%1));targets=[]
  for ob in cloth:
   v,m=row[ob.name];d=project(v,tree,corr[ob.name][i],ob['chain_index']>0 and not death_only);mx=max(mx,float(np.linalg.norm(d)));assert np.linalg.norm(d)<.40,(a.name,ob.name,float(f),d)
   m.translation+=Vector(d);targets.append((ob.vertex_groups[0].name,m))
  # Parent first, then child's absolute pose: a correction never gets applied twice down a strip.
  for bn,m in targets:armik.set_world(r,bn,m);keys.append((float(f),bn,r.pose.bones[bn].matrix_basis.copy()))
 previous={}
 for f,bn,m in keys:
  b=r.pose.bones[bn];q=m.to_quaternion()
  if bn in previous and q.dot(previous[bn])<0:q=-q
  previous[bn]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if 'B_ForgeApron_' in fc.data_path:
      for k in fc.keyframe_points:k.interpolation='LINEAR'
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_apron_surface_checkpoint.blend'));report[a.name]={'max_surface_correction_m':mx};print('HULL_SURFACE_FIT',a.name,mx,flush=True)
(P/'review/forge_apron_surface_fit.json').write_text(json.dumps(report,indent=2)+'\n');sys.stdout.flush();os._exit(0)
