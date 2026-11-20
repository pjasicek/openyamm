"""Promote the accepted LOD, repair the two toe roots, and unwrap body/wings independently."""
import bpy, bmesh, json, math, shutil, sys
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(Path('tools').resolve()),str(P.parent/'mm6_bar1_claude/scripts')]
from build_actor_lods import read_glb, accessor_bytes
import common
W=P/'work/parts_v5';W.mkdir(exist_ok=True)
R=P/'review/parts_v5';R.mkdir(exist_ok=True)
for f in ['mm6_gar.blend','mm6_gar_lods.glb','mm6_gar.glb']:
 if not (W/f).exists():shutil.copyfile(P/'export'/f,W/f)
bpy.ops.wm.open_mainfile(filepath=str(W/'mm6_gar.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
high=bpy.data.objects['Gargoyle'];rubble=bpy.data.objects['Rubble']
original=np.array([v.co[:] for v in high.data.vertices]);high.data.calc_loop_triangles()
tri=np.array([t.vertices[:] for t in high.data.loop_triangles]);tree=BVHTree.FromPolygons(original,tri,all_triangles=True)
def blend_roots(obj):
 co=np.array([v.co[:] for v in obj.data.vertices]);before=co.copy();canonical=co.copy();neg=canonical[:,0]<0
 canonical[neg,0]=-canonical[neg,0]-.061;canonical[neg,1]-=.084
 d=np.linalg.norm((canonical-[.295,.138,.075])/[.05,.085,.065],axis=1)
 weight=np.minimum(np.clip(1-d,0,1)*3,1)*.65
 adj=[set() for _ in co]
 for edge in obj.data.edges:
  a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
 for _ in range(55):
  out=co.copy()
  for i in np.where(weight>0)[0]:
   if adj[i]:out[i]=co[i]*(1-weight[i])+co[list(adj[i])].mean(0)*weight[i]
  co=out
 for v,pt in zip(obj.data.vertices,co):v.co=pt
 obj.data.update()
 return co-before
displacement=blend_roots(high);blend_roots(rubble)
print('ROOT_DISPLACEMENT',float(np.linalg.norm(displacement,axis=1).max()),flush=True)
assert np.max(np.linalg.norm(displacement,axis=1))<.12
high.data.calc_loop_triangles()
def nearest(pos):
 hit,normal,i,dist=tree.find_nearest(Vector(pos));v0,v1,v2=original[tri[i]];u,v=v1-v0,v2-v0;q=np.array(hit)-v0
 gram=np.array([[u@u,u@v],[u@v,v@v]])
 if abs(np.linalg.det(gram))<1e-18:w=np.array([1.,0,0])
 else:s,t=np.linalg.solve(gram,np.array([q@u,q@v]));w=np.array([1-s-t,s,t])
 return i,w
d,b=read_glb(W/'mm6_gar_lods.glb')
def arr(i):
 a=d['accessors'][i];code={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
 return np.frombuffer(accessor_bytes(d,b,i),dtype=code).reshape(a['count'],-1)
node=next(n for n in d['nodes'] if n.get('name')=='Gargoyle');joints=[d['nodes'][i]['name'] for i in d['skins'][node['skin']]['joints']]
source_co=[];source_n=[];source_faces=[]
for primitive in d['meshes'][node['mesh']]['primitives']:
 at=primitive['attributes'];c=arr(at['POSITION'])[:,[0,2,1]].copy();c[:,1]*=-1
 n=arr(at['NORMAL'])[:,[0,2,1]].copy();n[:,1]*=-1
 source_faces.extend((arr(primitive['indices']).reshape(-1,3)+len(source_co)).tolist());source_co.extend(c);source_n.extend(n)
source_co=np.array(source_co);source_n=np.array(source_n);source_faces=np.array(source_faces)
assert np.isfinite(source_n).all() and np.min(np.linalg.norm(source_n,axis=1))>.99
normal_tree=BVHTree.FromPolygons(source_co,source_faces,all_triangles=True)
from mathutils.geometry import barycentric_transform
def normal_at(pos):
 hit,_,fi,_=normal_tree.find_nearest(Vector(pos));ids=source_faces[fi]
 n=barycentric_transform(hit,*[Vector(p) for p in source_co[ids]],*[Vector(p) for p in source_n[ids]])
 assert n.length>.1 and np.isfinite(n[:]).all()
 return n.normalized()
mesh=next(m for m in d['meshes'] if m.get('name')=='Gargoyle_LOD1');parts=[]
for prim in mesh['primitives']:
 at=prim['attributes'];pos=arr(at['POSITION'])[:,[0,2,1]].copy();pos[:,1]*=-1
 uv=arr(at['TEXCOORD_0']).copy();uv[:,1]=1-uv[:,1];faces=arr(prim['indices']).reshape(-1,3)
 ns=[]
 for vi,pt in enumerate(pos.copy()):
  ti,w=nearest(pt);pos[vi]+=w@displacement[tri[ti]];ns.append(normal_at(pt))
 name='Head' if prim['material']==1 else 'Body'
 data=bpy.data.meshes.new(name+'Reduced');data.from_pydata(pos,[],faces);data.update()
 obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);obj.parent=rig
 mod=obj.modifiers.new('Armature','ARMATURE');mod.object=rig
 data.materials.append(high.data.materials[prim['material']]);uvlayer=data.uv_layers.new(name='UVMap')
 for poly in data.polygons:
  poly.use_smooth=True
  for li in poly.loop_indices:uvlayer.data[li].uv=uv[data.loops[li].vertex_index]
 data.normals_split_custom_set_from_vertices(ns)
 for n in joints:obj.vertex_groups.new(name=n)
 for suffix in ['0','1']:
  if 'JOINTS_'+suffix not in at:continue
  ji=arr(at['JOINTS_'+suffix]);we=arr(at['WEIGHTS_'+suffix])
  for vi in range(len(pos)):
   for j,w in zip(ji[vi],we[vi]):
    if w>0:obj.vertex_groups[int(j)].add([vi],float(w),'ADD')
 parts.append(obj)
assert sum(len(o.data.polygons) for o in parts)==7247
bpy.data.objects.remove(high,do_unlink=True)
body,head=[next(o for o in parts if o.name==n) for n in ['Body','Head']]
# Wing ownership comes from the fitted wing bones, including the soft root transition.
wing=np.array([sum(g.weight for g in v.groups if body.vertex_groups[g.group].name.startswith('W_')) for v in body.data.vertices])
wingfaces={f.index for f in body.data.polygons if wing[list(f.vertices)].mean()>.015}
assert 100<len(wingfaces)<len(body.data.polygons)//2,len(wingfaces)
wings=body.copy();wings.data=body.data.copy();wings.name='Wings';bpy.context.scene.collection.objects.link(wings)
for obj,keep in [(body,False),(wings,True)]:
 bm=bmesh.new();bm.from_mesh(obj.data);bm.faces.ensure_lookup_table()
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if (f.index in wingfaces)!=keep],context='FACES')
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
 bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-6);bm.to_mesh(obj.data);bm.free()
 obj.data.materials.clear();mat=bpy.data.materials.new('Gargoyle'+obj.name);mat.diffuse_color=(.45,.45,.45,1);obj.data.materials.append(mat)
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
 bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=.004,area_weight=0,correct_aspect=True,scale_to_bounds=True)
 bpy.ops.object.mode_set(mode='OBJECT')
 # BMesh changes corner indices; restore the high surface normals after welding/unwrapping.
 ns=[]
 for vertex in obj.data.vertices:
  ns.append(normal_at(vertex.co) if vertex.co.z>.22 else vertex.normal.copy())
 obj.data.normals_split_custom_set_from_vertices(ns)
 uv=obj.data.uv_layers.active.data;obj.data.calc_loop_triangles()
 np.savez(W/(obj.name.lower()+'_uv3d.npz'),uv=np.array([[uv[li].uv[:] for li in tr.loops] for tr in obj.data.loop_triangles]),xyz=np.array([[obj.data.vertices[i].co[:] for i in tr.vertices] for tr in obj.data.loop_triangles]),part=np.ones(len(obj.data.loop_triangles),int)*(3 if keep else 1))
 # Upload only the requested part; immutable head textures remain on the master.
 dup=obj.copy();dup.data=obj.data.copy();dup.parent=None;dup.modifiers.clear();dup.vertex_groups.clear();bpy.context.scene.collection.objects.link(dup)
 bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
 bpy.ops.export_scene.gltf(filepath=str(P/f'texturing/{obj.name.lower()}_v5_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False)
 bpy.data.objects.remove(dup,do_unlink=True)
 request={'model_url':f'@file:texturing/{obj.name.lower()}_v5_upload.glb','image_style_url':'@file:references_hd/00_three_quarter.png','ai_model':'meshy-7','enable_original_uv':True,'enable_pbr':True,'texture_resolution':'4k','target_formats':['glb'],'alpha_thumbnail':True}
 (P/f'requests/{obj.name.lower()}_texture_v5.json').write_text(json.dumps(request,indent=2)+'\n')
report={'triangles':{o.name:len(o.data.polygons) for o in [body,wings,head]},'foot_root_vertices':int(np.count_nonzero(np.linalg.norm(displacement,axis=1)>1e-6)),'max_foot_root_change_m':float(np.linalg.norm(displacement,axis=1).max()),'head_uv_preserved':True,'animations_preserved':True,'runtime_texture_resolution':{'body':1024,'wings':1024,'head':1024}}
(W/'preparation.json').write_text(json.dumps(report,indent=2))
for obj in bpy.data.objects:
 if obj.type=='MESH':obj.hide_render=obj==rubble
common.workbench_clay(bpy.context.scene)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'parts.blend'))
rig.animation_data.action=bpy.data.actions['Flight'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
scene=bpy.context.scene;scene.render.resolution_x=1100;scene.render.resolution_y=800
for name,eye,target,scale in [('feet_side',(2,-.4,.7),(.3,.1,.4),1.1),('feet_below',(.8,-1.5,-.1),(0,.15,.35),1.0),('feet_front',(0,-2,.8),(0,.1,.4),1.0)]:
 data=bpy.data.cameras.new(name);data.type='ORTHO';data.ortho_scale=scale;cam=bpy.data.objects.new(name,data);scene.collection.objects.link(cam);cam.location=eye;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam;scene.render.filepath=str(R/(name+'.png'));bpy.ops.render.render(write_still=True)
print('PARTS_V5',json.dumps(report))
