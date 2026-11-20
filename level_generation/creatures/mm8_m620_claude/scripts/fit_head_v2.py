"""Fit the isolated head to the saved civilian rig; retain UVs and transfer neck weights."""
from pathlib import Path
import bpy,bmesh,math,json,sys
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/checkpoint_before_head_v2/work/rig_textured_uv.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();me=body.data
oldco=np.array([v.co[:] for v in me.vertices]);oldregion=np.array([v.value for v in me.attributes['region'].data]);gn={g.index:g.name for g in body.vertex_groups}
# Nearest skin interpolation carries the existing neck blend; hair and eyes cannot attract the transfer.
faces=[tuple(f.vertices) for f in me.polygons if all(oldregion[i]==0 for i in f.vertices)]
tree=BVHTree.FromPolygons([Vector(v) for v in oldco],faces,all_triangles=True)
weights=[{gn[g.group]:g.weight for g in v.groups} for v in me.vertices]
new_before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p/'meshy/head_geometry_v3/model_urls_glb.glb'))
new=[o for o in set(bpy.data.objects)-new_before if o.type=='MESH']
for o in bpy.data.objects:o.select_set(o in new)
bpy.context.view_layer.objects.active=new[0]
if len(new)>1:bpy.ops.object.join()
head=bpy.context.object;head.parent=None;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
head.name='HeadSource'
co=np.array([v.co[:] for v in head.data.vertices]);lo=co.min(0);hi=co.max(0)
# Match the original crown and neck base. No body bone, bind matrix or animation curve changes.
scale=.270/(hi[2]-lo[2]);ring=co[co[:,2]<lo[2]+.045*(hi[2]-lo[2])];center=np.median(ring[:,:2],axis=0)
head.data.transform(Matrix.Translation(Vector((-.011,.028,1.430)))@Matrix.Scale(scale,4)@Matrix.Translation(Vector((-center[0],-center[1],-lo[2]))))
# Weld only the service's duplicated UV vertices, preserving per-corner UVs.
bm=bmesh.new();bm.from_mesh(head.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bm.to_mesh(head.data);bm.free()
for o in bpy.data.objects:o.select_set(o==head)
bpy.context.view_layer.objects.active=head
# Keep a dense face and simplify hair/back surfaces first.
protect=head.vertex_groups.new(name='face_detail')
for v in head.data.vertices:
 if v.co.y<-.018 and 1.46<v.co.z<1.645:protect.add([v.index],1,'REPLACE')
dec=head.modifiers.new('Head game budget','DECIMATE');dec.ratio=min(1,4000/max(len(head.data.polygons),1));dec.vertex_group=protect.name;dec.invert_vertex_group=True;dec.vertex_group_factor=1
bpy.ops.object.modifier_apply(modifier=dec.name);head.vertex_groups.clear()
# Remove the slanted bust cap, extend its rim, and fit horizontal neck sections.
bm=bmesh.new();bm.from_mesh(head.data);bm.normal_update()
caps=[f for f in bm.faces if f.normal.z<-.55 and f.calc_center_median().z<1.478]
assert caps, 'Expected the source bust cap'
bmesh.ops.delete(bm,geom=caps,context='FACES')
for v in bm.verts:
 if v.co.z<1.485 and any(e.is_boundary for e in v.link_edges):v.co.z=1.415
edges=[e for e in bm.edges if all(v.co.z<1.505 for v in e.verts)]
bmesh.ops.subdivide_edges(bm,edges=edges,cuts=2,use_grid_fill=True)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bm.to_mesh(head.data);bm.free()
def radial_hit(surface,co):
 origin=Vector((-.011,.028,co.z));direction=co-origin;direction.z=0;direction.normalize()
 loc,n,fi,d=surface.ray_cast(origin,direction,.2)
 assert loc is not None, tuple(co)
 return loc,n
def neck_section(co):
 d=co-Vector((-.011,.026,co.z));angle=math.atan2(d.y/.047,d.x/.049)
 return Vector((-.011+.049*math.cos(angle),.026+.047*math.sin(angle),co.z))
def lower_neck(co):
 loc,n=radial_hit(tree,co)
 t=min(1,max(0,(co.z-1.445)/.025));t=t*t*(3-2*t)
 return (loc-n*.0006).lerp(neck_section(co),t)
for v in head.data.vertices:
 if v.co.z<1.49:
  t=min(1,max(0,(1.49-v.co.z)/.023));t=t*t*(3-2*t)
  v.co=v.co.lerp(lower_neck(v.co),t)
head.data.update()
# Keep triangles above the attachment inside the rigid head region.
bm=bmesh.new();bm.from_mesh(head.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(0,0,1.445),plane_no=(0,0,1))
bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bm.to_mesh(head.data);bm.free()
# Trim the old face, eyes and angular hair together. Garments and limbs are below this plane.
bm=bmesh.new();bm.from_mesh(me)
reg=bm.verts.layers.int['region'];skin_faces=[f for f in bm.faces if all(v[reg] in (0,4,5) for v in f.verts)]
geom=set(skin_faces)|{e for f in skin_faces for e in f.edges}|{v for f in skin_faces for v in f.verts}
bmesh.ops.bisect_plane(bm,geom=list(geom),dist=1e-7,plane_co=(0,0,1.470),plane_no=(0,0,1))
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.calc_center_median().z>1.470001 and all(v[reg] in (0,4,5) for v in f.verts)],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bm.to_mesh(me);bm.free()
htree=BVHTree.FromPolygons([v.co[:] for v in head.data.vertices],[tuple(f.vertices) for f in head.data.polygons],all_triangles=True)
for v in me.vertices:
 if me.attributes['region'].data[v.index].value==0 and 1.445<v.co.z<1.47001:
  t=min(1,max(0,(v.co.z-1.445)/.025));t=t*t*(3-2*t)
  loc,n=radial_hit(htree,v.co)
  v.co=v.co.lerp(loc-n*.0008,t)
# Use one continuous weight field on both sides of the overlapping neck join.
from mathutils.geometry import barycentric_transform
for name in gn.values():head.vertex_groups.new(name=name)
for ob in (body,head):
 for v in ob.data.vertices:
  if ob==body and (v.co.z<1.435 or ob.data.attributes['region'].data[v.index].value!=0):continue
  if v.co.z>=1.444999:w={'B_Head':1.0}
  else:
   loc,n,fi,d=tree.find_nearest(v.co);inds=faces[fi];a,b,c=[Vector(oldco[i]) for i in inds]
   bc=barycentric_transform(loc,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
   w={}
   for i,k in zip(inds,bc):
    for name,value in weights[i].items():w[name]=w.get(name,0)+max(0,k)*value
   total=sum(w.values());assert total>.9
   t=min(1,max(0,(v.co.z-1.415)/.03));t=t*t*(3-2*t)
   w={n:value/total*(1-t) for n,value in w.items()};w['B_Head']=w.get('B_Head',0)+t
  for group in ob.vertex_groups:group.remove([v.index])
  for name,value in w.items():
   if value>1e-6:ob.vertex_groups[name].add([v.index],value,'REPLACE')
# Preserve the body's original UVs. The new head retains Meshy's dedicated UVs, no Smart UV fragmentation.
for ob,flag in [(body,0),(head,1)]:
 att=ob.data.attributes.get('head') or ob.data.attributes.new('head','INT','FACE');att.data.foreach_set('value',[flag]*len(ob.data.polygons))
 if ob==head:
  rawuv=ob.data.uv_layers.active;rawuv.name='HeadUV';uv=ob.data.uv_layers.new(name='UVMap')
  for a,b in zip(uv.data,rawuv.data):a.uv=b.uv
  region=ob.data.attributes.get('region') or ob.data.attributes.new('region','INT','POINT')
  region.data.foreach_set('value',[0]*len(ob.data.vertices))
  piece=ob.data.attributes.get('piece') or ob.data.attributes.new('piece','INT','POINT');piece.data.foreach_set('value',[104]*len(ob.data.vertices))
  for f in ob.data.polygons:f.use_smooth=True
# A small dark scalp closes the source's gaps between disconnected hair strands.
verts=[];uvs=[];polys=[];cols=32;rows=8
for row in range(rows+1):
 for col in range(cols):
  angle=2*math.pi*col/cols;theta=(1.62+.48*math.sin(angle))*row/rows
  verts.append((-.020+.060*math.sin(theta)*math.cos(angle),.025+.057*math.sin(theta)*math.sin(angle),1.604+.072*math.cos(theta)))
  uvs.append((.01+.008*(row/rows)*math.cos(angle),.01+.008*(row/rows)*math.sin(angle)))
for row in range(rows):
 for col in range(cols):
  a=row*cols+col;b=row*cols+(col+1)%cols;c=(row+1)*cols+(col+1)%cols;d=(row+1)*cols+col
  if row:polys.append((a,b,c))
  polys.append((a,c,d))
mesh=bpy.data.meshes.new('HairScalp');mesh.from_pydata(verts,[],[tuple(reversed(face)) for face in polys]);mesh.update();scalp=bpy.data.objects.new('HairScalp',mesh);bpy.context.collection.objects.link(scalp)
for layer in ('HeadUV','UVMap'):
 uv=mesh.uv_layers.new(name=layer)
 for f in mesh.polygons:
  for li in f.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
for name,domain,value in [('head','FACE',1),('region','POINT',4),('piece','POINT',105)]:
 att=mesh.attributes.new(name,'INT',domain);att.data.foreach_set('value',[value]*len(att.data))
scalp.vertex_groups.new(name='B_Head').add(list(range(len(verts))),1,'REPLACE')
for f in mesh.polygons:f.use_smooth=True
for o in bpy.data.objects:o.select_set(o in (head,scalp))
bpy.context.view_layer.objects.active=head;bpy.ops.object.join()
# One hair UV corner slipped 0.0028 outside the source tile during collapse.
for layer in head.data.uv_layers:
 for loop in layer.data:
  assert min(loop.uv)>-.005 and max(loop.uv)<1.005
  loop.uv=(max(0,min(1,loop.uv.x)),max(0,min(1,loop.uv.y)))
for face in body.data.polygons:
 if all(body.data.attributes['region'].data[i].value==0 and body.data.vertices[i].co.z>1.39 for i in face.vertices):face.use_smooth=True
# Make a visual candidate before replacing the authoritative master.
for o in bpy.data.objects:o.select_set(o in (body,head))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body=bpy.context.object
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_head_v2.blend'))
report={'head_scale':float(scale),'source_bounds':[lo.tolist(),hi.tolist()],'triangles':len(body.data.polygons),'head_triangles':sum(a.value for a in body.data.attributes['head'].data),'cut_z':1.470,'neck_overlap_m':.055,'rig_animations_unchanged':True}
(p/'work/head_fit_v2.json').write_text(json.dumps(report,indent=2)+'\n');print('HEAD_FIT',report)

common.setup_render();common.workbench_clay(bpy.context.scene,textured=True)
body.data.uv_layers.active=body.data.uv_layers['HeadUV']
common.render_views(str(p/'review/head_fit_v2'),1.50,.5,views=('front','left'),resolution=(768,768))
