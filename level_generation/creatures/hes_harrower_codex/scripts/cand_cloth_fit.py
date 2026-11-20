"""Fit the simulated cloth's actual skinned surface to the body and floor using its own bones."""
from pathlib import Path
import bpy,numpy as np,json,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
source=Path(args[0]).resolve() if args else P/'work/motion_final.blend'
output=Path(args[1]).resolve() if len(args)>1 else P/'work/motion_fitted.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
cloth=[o for o in bpy.data.objects if o.name.startswith(('Cloth_','Mantle_')) and o.type=='MESH']
rig.animation_data.action=None;bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for ob in cloth:
 for k in range(3):rig.data.edit_bones[ob.name+'_'+str(k)].use_connect=False
bpy.ops.object.mode_set(mode='OBJECT')
BF=[tuple(f.vertices) for f in body.data.polygons]
DIRS=[Vector(v).normalized() for v in ((.0123,.0217,1),(.71,-.33,-.62),(-.55,.81,.2),(.12,-.97,.21),(-.83,-.18,-.52))]
def coords(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.array([list(ob.matrix_world@p.co) for p in me.vertices]);ev.to_mesh_clear();return v
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
DATA={}
for ob in cloth:
 names=[ob.name+'_'+str(i) for i in range(3)];W=np.zeros((len(ob.data.vertices),3));rest=np.array([list(v.co) for v in ob.data.vertices]);test=rest[:,2]<rest[:,2].max()-.08
 for v in ob.data.vertices:
  for g in v.groups:W[v.index,names.index(ob.vertex_groups[g.group].name)]=g.weight
 DATA[ob.name]=(names,W,test)
def project(V,W,test,tree,D):
 inv_cost=np.array([.125,.5,1.])
 for iteration in range(30):
  worst=0.
  for i,w in enumerate(W):
   p=V[i]+w@D;delta=np.zeros(3)
   if p[2]<.004:delta[2]=.004-p[2]
   q=p+delta
   if test[i]:
    loc,n,fi,dist=tree.find_nearest(Vector(q),.12)
    if loc is not None and ((dist>.0003 and (Vector(q)-loc).dot(n)<-.5*dist and inside(tree,q)) or dist<.015):delta+=np.array(loc+n*.02)-q
   if np.linalg.norm(delta)>1e-6:
    D+=(w*inv_cost/(np.sum(w*w*inv_cost)+1e-12))[:,None]*delta;worst=max(worst,float(np.linalg.norm(delta)))
  if worst<.001:break
 return D
# Fit the same interpolation that glTF uses; changing it after fitting moved hems back into the tail.
for action in [a for a in bpy.data.actions if a.name.startswith('Harrower_Cand')]:
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
report={}
for a in [a for a in bpy.data.actions if a.name.startswith('Harrower_Cand')]:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];n=round(float(a.frame_range[1])*4);cache=[];corr={o.name:[] for o in cloth}
 for f in range(n+1):
  sc.frame_set(f//4,subframe=(f%4)/4);tree=BVHTree.FromPolygons(coords(body).tolist(),BF);frame={}
  for ob in cloth:
   names,W,test=DATA[ob.name];V=coords(ob);M=[armik.W(rig,name).copy() for name in names];D=project(V,W,test,tree,np.zeros((3,3)));corr[ob.name].append(D);frame[ob.name]=(V,M)
  cache.append((tree,frame))
 # Smooth corrections, then restore any surface constraints the smoothing relaxed.
 for name,ds in corr.items():
  ds=np.array(ds);radius=6;weights=np.exp(-.5*(np.arange(-radius,radius+1)/2.6)**2);weights/=weights.sum();idx=np.clip(np.arange(n+1)[:,None]+np.arange(-radius,radius+1),0,n)
  corr[name]=(ds[idx]*weights[None,:,None,None]).sum(1)
 keys={};maximum=0.;over={}
 for f,(tree,frame) in enumerate(cache):
  sc.frame_set(f//4,subframe=(f%4)/4)
  for ob in cloth:
   names,W,test=DATA[ob.name];V,matrices=frame[ob.name];D=project(V,W,test,tree,corr[ob.name][f]);maximum=max(maximum,float(np.linalg.norm(D,axis=1).max()))
   if np.linalg.norm(D,axis=1).max()>=.35:over.setdefault(ob.name,[]).append(f/4)
   for name,M,offset in zip(names,matrices,D):
    q=rig.pose.bones[name].rotation_quaternion.copy();scale=rig.pose.bones[name].scale.copy();N=M.copy();N.translation+=Vector(offset);armik.set_world(rig,name,N);loc=rig.pose.bones[name].location.copy();rig.pose.bones[name].rotation_quaternion=q;rig.pose.bones[name].scale=scale;keys[(f/4,name)]=loc
 for (f,name),loc in keys.items():rig.pose.bones[name].location=loc;rig.pose.bones[name].keyframe_insert('location',frame=f)
 
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 report[a.name]={'max_bone_surface_correction_m':maximum,'over_35cm_frames':over};print('CLOTH_FIT',a.name,round(maximum,4),flush=True)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output))
(P/'review/cand_cloth_fit.json').write_text(json.dumps(report,indent=2)+'\n')
