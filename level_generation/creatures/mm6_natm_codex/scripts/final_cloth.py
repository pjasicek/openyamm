import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from collision import inside
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_precloth.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;me=body.data
co=np.array([tuple(v.co)for v in me.vertices]);pv=np.array([d.value for d in me.attributes['piece'].data]);me.calc_loop_triangles();tri=np.array([list(t.vertices)for t in me.loop_triangles]);skintri=tri[np.all(pv[tri]==0,axis=1)];bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[.5,0,.5],[0,.5,.5],[1/3]*3]);chains={}
for part,name in [(1,'ClothFront'),(10,'ClothBack')]:
 bones=[name]+[name+str(i)for i in [1,2,3]];W=np.zeros((len(co),4))
 for v in me.vertices:
  for g in v.groups:
   n=body.vertex_groups[g.group].name
   if n in bones:W[v.index,bones.index(n)]=g.weight
 W[:,0]=W.sum(1);tt=tri[np.all(pv[tri]==part,axis=1)&(np.max(co[tri,2],axis=1)<.93)];chains[name]=(bones,W,tt)
a=bpy.data.actions['Death'];rows=[];poses=[];previous={n:np.zeros((4,3))for n in chains}
for f in range(int(a.frame_range[1])+1):
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(f);rig.animation_data.action=None
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();v=np.array([tuple(v.co)for v in mm.vertices]);ev.to_mesh_clear();tree=BVHTree.FromPolygons([Vector(p)for p in v],skintri.tolist(),all_triangles=True)
 for name,(bones,W,tt)in chains.items():
  pts=np.einsum('kj,tjd->tkd',bary,v[tt]).reshape(-1,3);weights=np.einsum('kj,tjd->tkd',bary,W[tt]).reshape(-1,4);delta=previous[name]*.90
  for iteration in range(160):
   changed=0
   for original,w in zip(pts,weights):
    p=original+w@delta;den=w@w
    if den<.0001:continue
    corr=Vector((0,0,max(0,.001-p[2])));q,n,idx,d=tree.find_nearest(Vector(p))
    if q is not None and (Vector(p)-q).dot(n)<-.00005 and inside(tree,Vector(p)):corr+=n*(d+.0007)
    if p[2]+corr.z<.001:corr.z=.001-p[2]
    if corr.length>.00005:delta+=np.outer(w,np.array(corr))*.45/den;changed+=1
   lengths=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,np.array([.2,.35,.35,.35])/np.maximum(lengths,1e-9))[:,None]
   if not changed:break
  previous[name]=delta.copy()
  for k,bn in enumerate(bones):
   pb=rig.pose.bones[bn];worldbasis=pb.matrix.to_3x3()@pb.rotation_quaternion.to_matrix().inverted();pb.location+=worldbasis.inverted()@Vector(delta[k])
  posed=pts+weights@delta;worst=0
  for pp in posed:
   q,n,idx,d=tree.find_nearest(Vector(pp))
   if q is not None and (Vector(pp)-q).dot(n)<-.00001 and inside(tree,Vector(pp)):worst=max(worst,d)
  rows.append({'frame':f,'panel':name,'floor_m':float(posed[:,2].min()),'penetration_m':worst,'max_additional_offset_m':float(np.linalg.norm(delta,axis=1).max())})
 poses.append({pb.name:(pb.location.copy(),pb.rotation_quaternion.copy())for pb in rig.pose.bones})
rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in list(bag.fcurves):
    if 'Cloth' in fc.data_path:bag.fcurves.remove(fc)
for f,pose in enumerate(poses):
 for bn in [n for c in chains.values()for n in c[0]]:
  l,q=pose[bn];pb=rig.pose.bones[bn];pb.location=l;pb.rotation_quaternion=q;pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
a=bpy.data.actions['Dead'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for f in [0,1]:
 for bn,(l,q)in poses[-1].items():
  pb=rig.pose.bones[bn];pb.location=l;pb.rotation_quaternion=q;pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_lod0.blend'));(P/'review/final_lod0/cloth_floor.json').write_text(json.dumps(rows,indent=2));print('CLOTH FLOOR',min(r['floor_m']for r in rows),max(r['penetration_m']for r in rows),max(r['max_additional_offset_m']for r in rows),flush=True)
