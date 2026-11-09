"""Restore the original arm topology/weights; retain the current body, face and animation data."""
import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_feedback_v2/textured_uv.blend'))
o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];old=o.data;r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();source=np.load(P/'work/forearms_dense.npz');sc=source['co'];sp=source['piece'];sf=source['faces'];sw=source['weights'];sn=list(source['names']);gn={g.name:g.index for g in o.vertex_groups}
opc=np.array([v.value for v in old.attributes['piece'].data]);oc=np.array([v.co[:] for v in old.vertices]);of=np.array([list(f.vertices) for f in old.polygons]);ouv=np.array([[old.uv_layers['UVMap'].data[i].uv[:] for i in f.loop_indices] for f in old.polygons]);ohuv=np.array([[old.uv_layers['HeadUV'].data[i].uv[:] for i in f.loop_indices] for f in old.polygons]);oh=np.array([v.value for v in old.attributes['head'].data])
# All unchanged faces retain both UV layouts. Matching hand triangles retain their existing skin detail.
kept=np.where(~np.isin(opc,[4,5]))[0];dense=np.where(np.isin(sp,[4,5]))[0];coords=np.concatenate([oc[kept],sc[dense]]);pieces=np.concatenate([opc[kept],sp[dense]]);oldmap={int(v):i for i,v in enumerate(kept)};srcmap={int(v):len(kept)+i for i,v in enumerate(dense)}
faces=[];head=[];body_uv=[];head_uv=[];exact=[];src_face=[]
for f in old.polygons:
 if opc[f.vertices[0]] in [4,5]:continue
 faces.append([oldmap[i] for i in f.vertices]);head.append(int(oh[f.index]));body_uv.append(ouv[f.index]);head_uv.append(ohuv[f.index]);exact.append(True);src_face.append(f.index)
tree=KDTree(len(oc))
for i,c in enumerate(oc):tree.insert(Vector(c),i)
tree.balance();source_to_old={}
for i in dense:
 _,vi,dist=tree.find(Vector(sc[i]))
 if dist<1e-5 and opc[vi]==sp[i]:source_to_old[int(i)]=vi
face_lookup={tuple(sorted(f.vertices)):f.index for f in old.polygons if opc[f.vertices[0]] in [4,5]}
for f in sf:
 if sp[f[0]] not in [4,5]:continue
 faces.append([srcmap[int(i)] for i in f]);head.append(0);head_uv.append(np.zeros((3,2)));key=tuple(sorted(source_to_old.get(int(i),-1) for i in f));fi=face_lookup.get(key);src_face.append(-1 if fi is None else fi);exact.append(fi is not None)
 if fi is None:body_uv.append(np.zeros((3,2)))
 else:body_uv.append(np.array([ouv[fi,list(of[fi]).index(source_to_old[int(i)])] for i in f]))
me=bpy.data.meshes.new('BodyRestored');me.from_pydata(coords.tolist(),[],faces);me.update();o.data=me
for name,index in gn.items():assert o.vertex_groups.new(name=name).index==index
for name,domain,values in [('piece','POINT',pieces),('head','FACE',head)]:
 a=me.attributes.new(name,'INT',domain);a.data.foreach_set('value',values)
for name,values in [('UVMap',body_uv),('HeadUV',head_uv)]:
 layer=me.uv_layers.new(name=name)
 for f,uv in zip(me.polygons,values):
  for li,v in zip(f.loop_indices,uv):layer.data[li].uv=v
for new,vi in enumerate(kept):
 for g in old.vertices[int(vi)].groups:o.vertex_groups[g.group].add([new],g.weight,'REPLACE')
for vi in dense:
 for i,w in enumerate(sw[vi]):
  if w>1e-7:o.vertex_groups[gn[sn[i]]].add([srcmap[int(vi)]],float(w),'REPLACE')
# Keep the restored open ends safely inside the reduced sleeves; this band lies above the exposed elbow.
for side,part in [('L',4),('R',5)]:
 sh=r.data.bones[f'B_{side}_UpperArm'].head_local;el=r.data.bones[f'B_{side}_Forearm'].head_local;axis=(el-sh).normalized();group=o.vertex_groups[f'B_{side}_UpperArm']
 for v in me.vertices:
  if pieces[v.index]!=part:continue
  t=(v.co-sh).dot(axis);w=float(np.clip((.205-t)/.045,0,1))
  if w==0:continue
  center=sh+axis*t;rad=v.co-center;target=center+rad.normalized()*min(rad.length,.032)
  v.co=v.co.lerp(target,w);coords[v.index]=v.co[:]
  values={g.group:g.weight*(1-w) for g in v.groups};values[group.index]=values.get(group.index,0)+w
  for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
  for i,value in values.items():
   if value>1e-7:o.vertex_groups[i].add([v.index],value,'REPLACE')
for f in me.polygons:f.use_smooth=True
# Unwrap only restored triangles, then repack the body without rotating the retained tangent frames.
for ob in bpy.data.objects:ob.select_set(ob==o)
bpy.context.view_layer.objects.active=o;me.uv_layers.active=me.uv_layers['UVMap']
def select(ids):
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_mode(type='FACE');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
 for i in ids:me.polygons[i].select=True
 bpy.ops.object.mode_set(mode='EDIT')
select([i for i,x in enumerate(exact) if not x]);bpy.ops.uv.smart_project(angle_limit=math.radians(50),island_margin=.006);bpy.ops.object.mode_set(mode='OBJECT')
select([i for i,x in enumerate(head) if not x]);bpy.ops.uv.pack_islands(rotate=False,margin=.004);bpy.ops.object.mode_set(mode='OBJECT')
# A new chart is sampled through the old surface per texel; no extrapolated UV triangle can cross a seam.
trees={};source_faces={}
for part in [4,5]:
 inds=np.where(np.all(opc[of]==part,axis=1))[0];source_faces[part]=inds;trees[part]=BVHTree.FromPolygons([Vector(x) for x in oc],of[inds].tolist(),all_triangles=True)
N=2048;hits=np.zeros((N,N),np.uint8);srcuv=np.zeros((N,N,2),np.float32);replaced=np.zeros((N,N),bool);degenerate=0
for f in me.polygons:
 if head[f.index]:continue
 uv=np.array([me.uv_layers['UVMap'].data[i].uv[:] for i in f.loop_indices]);a,b,c=uv*N;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);assert abs(den)>1e-10
 x0,y0=np.maximum(np.floor(uv.min(0)*N).astype(int),0);x1,y1=np.minimum(np.ceil(uv.max(0)*N).astype(int),N-1);x,y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
 w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;w2=1-w0-w1;mask=(w0>1e-6)&(w1>1e-6)&(w2>1e-6);ix=(x[mask]-.5).astype(int);iy=N-1-(y[mask]-.5).astype(int);hits[iy,ix]+=1;weights=np.stack([w0[mask],w1[mask],w2[mask]],axis=1)
 if exact[f.index]:srcuv[iy,ix]=weights@body_uv[f.index]
 else:
  positions=weights@coords[list(f.vertices)];part=int(pieces[f.vertices[0]])
  for xx,yy,pt in zip(ix,iy,positions):
   q,n,fi,dist=trees[part].find_nearest(Vector(pt));oi=source_faces[part][fi];tri=oc[of[oi]];u=tri[1]-tri[0];v=tri[2]-tri[0];d=np.array(q)-tri[0];aa=u@u;bb=u@v;cc=v@v;div=aa*cc-bb*bb;j=(cc*(d@u)-bb*(d@v))/div;k=(aa*(d@v)-bb*(d@u))/div;srcuv[yy,xx]=np.array([1-j-k,j,k])@ouv[oi]
  replaced[iy,ix]=True
assert (hits>1).sum()==0,int((hits>1).sum())
np.savez_compressed(P/'work/body_reprojection.npz',coverage=hits>0,srcuv=srcuv,replaced=replaced)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forearms_repaired.blend'))
report={'triangles_before':len(old.polygons),'triangles_after':len(me.polygons),'restored_arm_faces':int(sum(sp[f[0]] in [4,5] for f in sf)),'restored_triangles_with_retained_uv':int(sum(exact)-sum(not np.isin(opc[f.vertices[0]],[4,5]) for f in old.polygons)),'new_body_uv_overlap_pixels':int((hits>1).sum()),'source':'work/clearance_v1.blend','method':'Original arm topology and weights, exact hand UV matches, surface reprojection for new triangles.','animation_curves':'unchanged'}
(P/'work/forearm_repair.json').write_text(json.dumps(report,indent=2));print('FOREARM_REPAIR',json.dumps(report),flush=True)
me.materials.clear();mat=bpy.data.materials.new('Clay');mat.diffuse_color=(.55,.55,.55,1);me.materials.append(mat)
for f in me.polygons:f.material_index=0
common.setup_render();common.workbench_clay(bpy.context.scene)
for clip,frame in [('Standing',0),('Walking',17),('Hit',4),('Fidget',48),('Death',18)]:
 a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(frame)
 common.render_views(str(P/'review/feedback_v2'/f'repaired_{clip}'),1.04,.75,views=('left','back'),target=(.26,.03),resolution=(650,850))
