"""Rebake the front tabard with a pinned waist, shared bend and temporally continuous clearance."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));from volume_contact import inside
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v10_geometry.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;sc=bpy.context.scene;sc.render.fps=30
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
C=np.flatnonzero(pv==9);co=np.array([v.co[:] for v in me.vertices]);chains=json.loads(sc['nobl_tabard'])
names=[n for c in chains for n in c['bones']]
def use(a):r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
def posed():
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.array([x.co[:] for x in m.vertices]);ev.to_mesh_clear();return v
# Pin the cloth's upper edge under the belt rather than translating its root per frame.
for i in C:
 w=float(np.clip((co[i,2]-.935)/.065,0,1))
 old={g.group:g.weight for g in me.vertices[i].groups}
 for g,val in old.items():o.vertex_groups[g].add([int(i)],val*(1-w),'REPLACE')
 o.vertex_groups['B_Pelvis'].add([int(i)],w,'ADD')
 if co[i,2]>1.005:me.vertices[i].co.y=max(me.vertices[i].co.y,-.157)
co=np.array([v.co[:] for v in me.vertices]);index={n:i for i,n in enumerate(names)}
weights=np.zeros((len(C),len(names)));pelvis=np.zeros(len(C))
for j,i in enumerate(C):
 for e in me.vertices[i].groups:
  name=o.vertex_groups[e.group].name
  if name in index:weights[j,index[name]]=e.weight
  elif name=='B_Pelvis':pelvis[j]=e.weight
assert np.max(abs(weights.sum(1)+pelvis-1))<1e-5
rest={n:r.data.bones[n].matrix_local.copy() for n in names};inv={n:np.array(rest[n].inverted()) for n in names}
pelrest=r.data.bones['B_Pelvis'].matrix_local.copy()
# One continuous sheet: neighbouring columns share the same curvature and cannot fight each other.
factors=[.60,.88,1.,1.]
def matrices(angle,pm):
 D=pm@pelrest.inverted();out={}
 for c in chains:
  head=D@Vector(c['pts'][0])
  for k,name in enumerate(c['bones']):
   rot=D.to_3x3()@Matrix.Rotation(-angle*factors[k],3,'X')@rest[name].to_3x3()
   length=r.data.bones[name].length
   if globals().get('role')=='Death':
    direction=rot@Vector((0,1,0))
    if head.z+direction.z*length<.029:
     dz=max(-1.,min(1.,(.029-head.z)/length))
     horizontal=Vector((direction.x,direction.y,0))
     if horizontal.length<1e-6:horizontal=Vector((0,1,0))
     horizontal.normalize();desired=horizontal*math.sqrt(max(0,1-dz*dz));desired.z=dz
     rot=direction.rotation_difference(desired).to_matrix()@rot
   M=rot.to_4x4();M.translation=head;out[name]=M
   head=M@Vector((0,length,0))
 return out
def vertices(angle,pm):
 mats=matrices(angle,pm);D=np.array(pm@pelrest.inverted())
 X=co[C]@D[:3,:3].T+D[:3,3];X*=pelvis[:,None]
 for n,M in mats.items():
  A=np.array(M)@inv[n];X+=(co[C]@A[:3,:3].T+A[:3,3])*weights[:,index[n],None]
 return X
faces=[tuple(f.vertices) for f in me.polygons if pv[f.vertices[0]] in [2,6,7]]
def bad_count(X,tree):
 bad=0
 for i,point in zip(C,X):
  if co[i,2]>.945:continue
  if point[2]<-.001:bad+=1;continue
  loc,normal,face,dist=tree.find_nearest(Vector(point),.10)
  if loc is not None and dist>.003 and (Vector(point)-loc).dot(normal)<0 and inside(tree,point):bad+=1
 return bad
report={}
roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
for role in roles:
 a=bpy.data.actions[role];use(a)
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in list(bag.fcurves):
     if any('["'+n+'"]' in fc.data_path for n in names):bag.fcurves.remove(fc)
 for n in names:r.pose.bones[n].matrix_basis.identity()
 frames=list(range(int(a.frame_range[1])+1));parents=[];trees=[];targets=[]
 for f in frames:
  sc.frame_set(f);pm=r.pose.bones['B_Pelvis'].matrix.copy();parents.append(pm)
  P=posed();tree=BVHTree.FromPolygons(P.tolist(),faces);trees.append(tree)
  best=None
  down=(pm@pelrest.inverted()).to_3x3()@Vector((0,0,-1))
  fall_min=max(0.,math.degrees(math.atan2(down.y,-down.z))/.6+6.)
  candidates=np.arange(min(178,2*math.ceil(fall_min/2)),182,2) if role=='Death' else np.arange(0,86,2)
  for degree in candidates:
   X=vertices(math.radians(float(degree)),pm);bad=bad_count(X,tree)
   candidate=(bad,abs(float(degree)),float(degree))
   if best is None or candidate<best:best=candidate
   if bad==0:break
  targets.append(math.radians(best[2]))
 # Smooth in angle space with an anticipatory upper envelope: no per-frame collision displacement.
 # Each clearance peak spreads across 0.3 seconds instead of creating a one-frame impulse.
 cyclic=role in ['Standing','Walking','Running','Fidget'];nframe=len(frames)-1 if cyclic else len(frames)
 target=np.array(targets[:nframe]);sigma=6.
 smooth=np.zeros(nframe)
 for i in range(nframe):
  dist=np.abs(np.arange(nframe)-i)
  if cyclic:dist=np.minimum(dist,nframe-dist)
  v=target*np.exp(-.5*(dist/sigma)**2)
  smooth[i]=v[np.argmax(abs(v))]
 # A short symmetric filter removes the envelope's derivative corners while retaining clearance.
 pad=np.pad(smooth,3,mode='wrap' if cyclic else 'edge');kernel=np.array([1,3,6,7,6,3,1],float);kernel/=kernel.sum()
 angles=np.convolve(pad,kernel,'valid')
 angles+=max(0,float(np.max(target-angles)))+.025 if target.max()>0 else 0
 if cyclic:angles=np.r_[angles,angles[0]]
 before=[];contacts=0
 for f,pm,angle,tree in zip(frames,parents,angles,trees):
  sc.frame_set(f);M=matrices(float(angle),pm)
  for name in names:
   pb=r.pose.bones[name];parent=pb.parent.name;P=M[parent] if parent in M else pm
   base=P@r.data.bones[parent].matrix_local.inverted()@rest[name]
   local=base.inverted()@M[name]
   pb.rotation_mode='QUATERNION';pb.rotation_quaternion=local.to_quaternion();pb.location=local.translation
   pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  bpy.context.view_layer.update()
  X=posed()[C];pred=vertices(float(angle),pm)
  assert np.max(np.linalg.norm(X-pred,axis=1))<.0001
  D=np.array((pm@pelrest.inverted()).inverted());before.append(X@D[:3,:3].T+D[:3,3])
  contacts+=bad_count(X,tree)
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     if any('["'+n+'"]' in fc.data_path for n in names):
      for key in fc.keyframe_points:key.interpolation='LINEAR'
 X=np.array(before);step=np.linalg.norm(np.diff(X,axis=0),axis=2);second=np.linalg.norm(np.diff(X,n=2,axis=0),axis=2)
 report[role]={'target_degrees':np.degrees(target).tolist(),'baked_degrees':np.degrees(angles).tolist(),'max_step_mm':float(step.max()*1000),'max_second_step_mm':float(second.max()*1000),'penetrating_samples':contacts}
 print('TABARD',role,'step mm',round(step.max()*1000,2),'second mm',round(second.max()*1000,2),'penetrating samples',contacts,flush=True)
 if role=='Death':
  death_pose={name:(r.pose.bones[name].rotation_quaternion.copy(),r.pose.bones[name].location.copy()) for name in names}
# Exact held death pose.
a=bpy.data.actions['Dead'];use(a)
for l in a.layers:
 for st in l.strips:
  for bag in st.channelbags:
   for fc in list(bag.fcurves):
    if any('["'+n+'"]' in fc.data_path for n in names):bag.fcurves.remove(fc)
for f in [0,30]:
 for name,(q,loc) in death_pose.items():
  b=r.pose.bones[name];b.rotation_quaternion=q;b.location=loc;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
# Remove facet normals on the repaired glove and gently fair the palm while keeping its cuff fixed.
for f in me.polygons:
 if pv[f.vertices[0]]==5:f.use_smooth=True
sc['tabard_feedback_repair']='Pinned pelvis edge, shared chain curvature, smoothed collision-clearance angle; no independent translation correction.'
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v10.blend'))
(p/'review/feedback_20261011/tabard_repair.json').write_text(json.dumps(report,indent=1))
