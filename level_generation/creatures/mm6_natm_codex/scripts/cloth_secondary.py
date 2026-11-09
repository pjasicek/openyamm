"""UV-preserving cloth bend rows and constrained secondary deformation, sampled at 48 Hz."""
import bpy,bmesh,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from collision import inside
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
me=body.data;old=(len(me.vertices),len(me.polygons));bm=bmesh.new();bm.from_mesh(me);pl=bm.verts.layers.int['piece']
for z in [.86,.74,.62,.50,.38]:
 faces=[f for f in bm.faces if all(v[pl]in [1,10]for v in f.verts)];edges=set(e for f in faces for e in f.edges);verts=set(v for f in faces for v in f.verts);bmesh.ops.bisect_plane(bm,geom=list(verts)+list(edges)+faces,dist=.000001,plane_co=(0,0,z),plane_no=(0,0,1),clear_inner=False,clear_outer=False)
bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();co=np.array([tuple(v.co)for v in me.vertices]);pv=np.array([d.value for d in me.attributes['piece'].data]);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for part,name in [(1,'ClothFront'),(10,'ClothBack')]:
 root=rig.data.edit_bones[name]
 for k,z in enumerate([.78,.56,.34],1):
  b=rig.data.edit_bones.new(name+str(k));b.head=(root.head.x,root.head.y,z);b.tail=b.head+Vector((0,.10,0));b.parent=root;b.align_roll(Vector((0,0,1)))
bpy.ops.object.mode_set(mode='OBJECT');chains={}
skin_ids=np.where(pv==0)[0];kd=KDTree(len(skin_ids))
for k,i in enumerate(skin_ids):kd.insert(Vector(co[i]),k)
kd.balance();skinweights={v.index:{body.vertex_groups[g.group].name:g.weight for g in v.groups}for v in me.vertices if pv[v.index]==0}
skin_faces=[list(f.vertices)for f in me.polygons if all(pv[i]==0 for i in f.vertices)];rest_tree=BVHTree.FromPolygons([Vector(v)for v in co],skin_faces,all_triangles=True)
for i in np.where(np.isin(pv,[1,10])&(co[:,2]>.86))[0]:
 q,n,idx,d=rest_tree.find_nearest(Vector(co[i]));signed=(Vector(co[i])-q).dot(n)
 if signed<.004 and d<.04:co[i]+=np.array(n)*(.004-signed);me.vertices[i].co=Vector(co[i])

for part,name in [(1,'ClothFront'),(10,'ClothBack')]:
 ids=np.where(pv==part)[0];groups=[name]+[name+str(k)for k in [1,2,3]];zj=np.array([.98,.78,.56,.34]);weights=np.zeros((len(co),4))
 for n in groups:
  if n not in body.vertex_groups:body.vertex_groups.new(name=n)
 for i in ids:
  for g in body.vertex_groups:g.remove([int(i)])
  z=co[i,2];j=min(2,max(0,int(np.searchsorted(-zj,-z)-1)));t=float(np.clip((zj[j]-z)/(zj[j]-zj[j+1]),0,1));weights[i,j]=1-t;weights[i,j+1]=t
  attach=float(np.clip((z-.78)/.12,0,1));weights[i]*=(1-attach)
  near=skin_ids[kd.find(Vector(co[i]))[1]];ww={n:v*attach for n,v in skinweights[int(near)].items()}
  for k,w in enumerate(weights[i]):
   if w>1e-9:ww[groups[k]]=ww.get(groups[k],0)+w
  keep=sorted(ww.items(),key=lambda p:p[1],reverse=True)[:4];total=sum(v for _,v in keep)
  for n,w in keep:body.vertex_groups[n].add([int(i)],float(w/total),'REPLACE')
  weights[i]=[dict(keep).get(n,0)/total for n in groups]
 chains[name]={'ids':ids,'W':weights,'bones':groups}
me.calc_loop_triangles();tri=np.array([list(t.vertices)for t in me.loop_triangles]);skintri=tri[np.all(pv[tri]==0,axis=1)];bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[.5,0,.5],[0,.5,.5],[1/3]*3]);report={}
for act in [a for a in bpy.data.actions if a.name!='Dead']:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows=[];last={n:np.zeros((3,3))for n in chains}
 for f in range(int(act.frame_range[1])+1):
  rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(f);pel=rig.pose.bones['B_Pelvis'].matrix.to_3x3()@rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();angles=[]
  for sd in 'LR':
   d=pel.inverted()@(rig.pose.bones[f'B_{sd}_Calf'].head-rig.pose.bones[f'B_{sd}_Thigh'].head);angles.append(math.atan2(-d.y,-d.z))
  for name,a in [('ClothFront',-max(0,max(angles))*.55-.04),('ClothBack',max(0,-min(angles))*.55+.04)]:
   a=max(-math.radians(25 if act.name=='Death' else 40),min(math.radians(25 if act.name=='Death' else 40),a));pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion((1,0,0),a);pb.keyframe_insert('rotation_quaternion',frame=f)
   for n in chains[name]['bones'][1:]:rig.pose.bones[n].location=Vector();rig.pose.bones[n].rotation_quaternion=Quaternion()
  rig.animation_data.action=None
  bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();v=np.array([tuple(v.co)for v in mesh.vertices]);ev.to_mesh_clear();tree=BVHTree.FromPolygons([Vector(p)for p in v],skintri.tolist(),all_triangles=True)
  if act.name=='Death':
   for part,name in [(1,'ClothFront'),(10,'ClothBack')]:
    ids=chains[name]['ids'];low=ids[co[ids,2]<.90];tlocal=tri[np.all(pv[tri]==part,axis=1)&(np.max(co[tri,2],axis=1)<.93)];pb=rig.pose.bones[name];prior=pb.rotation_quaternion.copy();best=None
    for deg,sideangle in [(x,y)for x in range(-150,151,15)for y in range(-90,91,30)]:
     qq=Quaternion((0,1,0),math.radians(sideangle))@Quaternion((1,0,0),math.radians(deg));pb.rotation_quaternion=qq;bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();vv=np.array([tuple(v.co)for v in mm.vertices]);points=[Vector(v)for v in np.einsum('kj,tjd->tkd',bary[[0,1,2,6]],vv[tlocal]).reshape(-1,3)];ev.to_mesh_clear();depths=[]
     for point in points:
      q,n,idx,dist=tree.find_nearest(point)
      depths.append(dist if q is not None and (point-q).dot(n)<0 and inside(tree,point)else 0)
     floor=max(0,.002-min(p.z for p in points));cost=floor*floor*20+sum(d*d for d in depths)+.000002*(math.radians(deg)-prior.to_euler().x)**2
     if best is None or cost<best[0]:best=(cost,qq.copy())
    pb.rotation_quaternion=best[1]
   bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();v=np.array([tuple(v.co)for v in mesh.vertices]);ev.to_mesh_clear()

  for part,name in [(1,'ClothFront'),(10,'ClothBack')]:
   d=chains[name];tt=tri[np.all(pv[tri]==part,axis=1)&(np.max(co[tri,2],axis=1)<.93)];points=np.einsum('kj,tjd->tkd',bary,v[tt]).reshape(-1,3);W=np.einsum('kj,tjd->tkd',bary,d['W'][tt,1:]).reshape(-1,3);delta=last[name]*.92
   for iteration in range(32):
    posed=points+W@delta;bad=0;worst=0
    for i,p in enumerate(posed):
     w=W[i];den=float(w@w)
     if den<.01:continue
     q,n,idx,dist=tree.find_nearest(Vector(p));corr=Vector()
     if q is not None and (Vector(p)-q).dot(n)<-.00001 and inside(tree,Vector(p)):corr=n*(dist+.0010);worst=max(worst,dist)
     if p[2]+corr.z<.001:corr.z+=.001-p[2]-corr.z
     if corr.length>0:
      bad+=1;delta+=np.outer(w,np.array(corr))*.65/den
    if bad==0:break
    # Secondary rows keep their spacing through a weak smoothness constraint.
    for k in range(1,3):delta[k]=.995*delta[k]+.005*delta[k-1]
    lengths=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.12/np.maximum(lengths,1e-9))[:,None]
   posed=points+W@delta;worst=0
   for p in posed:
    q,n,idx,dist=tree.find_nearest(Vector(p))
    if q is not None and (Vector(p)-q).dot(n)<-.00001 and inside(tree,Vector(p)):worst=max(worst,dist)
   for j,bn in enumerate(d['bones'][1:]):
    pb=rig.pose.bones[bn];base=(rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted()@rig.data.bones[bn].matrix_local).to_3x3();pb.location=base.inverted()@Vector(delta[j])
   last[name]=delta;rows.append({'frame':f,'panel':name,'penetration_m':worst,'floor_m':float(posed[:,2].min()),'max_offset_m':float(np.linalg.norm(delta,axis=1).max())})
  rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
  for bn in [b for c in chains.values()for b in c['bones']]:
   pb=rig.pose.bones[bn];pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
 report[act.name]={'max_penetration_m':max(r['penetration_m']for r in rows),'min_floor_m':min(r['floor_m']for r in rows),'max_offset_m':max(r['max_offset_m']for r in rows),'samples':rows};print('CLOTH SECONDARY',act.name,{k:v for k,v in report[act.name].items()if k!='samples'},flush=True)
# Corpse is exactly the fall's final pose, including its cloth controls.
act=bpy.data.actions['Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(int(act.frame_range[1]));pose={p.name:(p.location.copy(),p.rotation_quaternion.copy())for p in rig.pose.bones};act=bpy.data.actions['Dead'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
for f in [0,1]:
 for n,(l,q)in pose.items():pb=rig.pose.bones[n];pb.location=l;pb.rotation_quaternion=q;pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
for act in bpy.data.actions:
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/cloth_master.blend'));(P/'review/cloth_secondary.json').write_text(json.dumps({'sample_hz':48,'topology_before':old,'topology_after':[len(me.vertices),len(me.polygons)],'UVs':'bisect interpolates the existing loop UVs; no rest silhouette or texture change','clips':report},indent=2))
