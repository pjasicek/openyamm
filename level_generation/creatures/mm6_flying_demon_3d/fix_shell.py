"""Use Blender's exact self union on the body shell, keeping movable parts separate."""
from pathlib import Path
import bpy,bmesh,json
from mathutils import Vector
from mathutils.geometry import barycentric_transform
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_uv_master.blend'))
scene=bpy.context.scene;body=scene.objects['Flying_Demon_Body'];original=len(body.data.polygons)
bm=bmesh.new();bm.from_mesh(body.data);unseen=set(bm.verts);components=[]
while unseen:
 seed=next(iter(unseen));seen={seed};todo=[seed]
 while todo:
  v=todo.pop()
  for e in v.link_edges:
   u=e.other_vert(v)
   if u not in seen:seen.add(u);todo.append(u)
 unseen.difference_update(seen);components.append(seen)
main=max(components,key=len);main_ids={v.index for v in main};bm.free()
parts=[]
for name,keep_main in [('Temporary_Body_Shell',True),('Temporary_Movable_Parts',False)]:
 obj=body.copy();obj.data=body.data.copy();obj.name=name;obj.modifiers.clear();scene.collection.objects.link(obj)
 bm=bmesh.new();bm.from_mesh(obj.data)
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if (v.index in main_ids)!=keep_main],context='VERTS');bm.to_mesh(obj.data);bm.free();parts.append(obj)
shell,other=parts
# Boolean-created points need a deliberate transfer from the original shell.
source_coords=[v.co.copy() for v in shell.data.vertices]
source_faces=[list(f.vertices) for f in shell.data.polygons]
source_weights=[{g.group:g.weight for g in v.groups} for v in shell.data.vertices]
source_tree=BVHTree.FromPolygons(source_coords,source_faces,all_triangles=True)
group=bpy.data.node_groups.new('Exact_Union_Repair','GeometryNodeTree')
group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
i=group.nodes.new('NodeGroupInput');o=group.nodes.new('NodeGroupOutput');boolean=group.nodes.new('GeometryNodeMeshBoolean');boolean.operation='UNION';boolean.solver='EXACT'
next(s for s in boolean.inputs if s.identifier=='Self Intersection').default_value=True
group.links.new(i.outputs['Geometry'],next(s for s in boolean.inputs if s.identifier=='Mesh 2'));group.links.new(boolean.outputs['Mesh'],o.inputs['Geometry'])
for obj in scene.objects:obj.select_set(obj==shell)
bpy.context.view_layer.objects.active=shell;mod=shell.modifiers.new('Exact self union','NODES');mod.node_group=group;bpy.ops.object.modifier_apply(modifier=mod.name)
other.select_set(True);bpy.ops.object.join()
assert [g.name for g in shell.vertex_groups]==[g.name for g in body.vertex_groups]
body.data=shell.data;bpy.data.objects.remove(shell,do_unlink=True)
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
body.data.validate(verbose=True,clean_customdata=False)
# The original pendant hinge left five small residual weights after deletion.
# Move those missing fractions onto Spine1, matching the removed clasp surface.
spine=body.vertex_groups['mixamorig:Spine1'];transferred=0
for v in body.data.vertices:
 if sum(g.weight for g in v.groups)>1e-7:continue
 point,normal,index,distance=source_tree.find_nearest(v.co);assert point is not None and distance<.00001,(v.index,distance)
 ids=source_faces[index];a,b,c=[source_coords[i] for i in ids]
 bary=barycentric_transform(point,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
 mixed={}
 for i,factor in zip(ids,bary):
  for g,w in source_weights[i].items():mixed[g]=mixed.get(g,0)+max(0,factor)*w
 selected=sorted(mixed.items(),key=lambda x:-x[1])[:8];total=sum(w for g,w in selected);assert total>.98
 for g,w in selected:body.vertex_groups[g].add([v.index],w/total,'REPLACE')
 transferred+=1
for v in body.data.vertices:
 total=sum(g.weight for g in v.groups)
 if total<.99999:
  assert total>.98,(v.index,total)
  w=next((g.weight for g in v.groups if g.group==spine.index),0);spine.add([v.index],w+1-total,'REPLACE')
body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops))
for f in body.data.polygons:f.use_smooth=True
row={'method':'Blender exact self union of the principal body shell; independently articulated eyes, jaw, ears and teeth preserved as separate components.',
 'original_triangles':original,'final_triangles':len(body.data.polygons),'independent_parts_preserved':len(components)-1,'rig_and_animation_unchanged':True,'new_vertices_with_barycentric_skin_transfer':transferred}
(P/'work/chest_surface_repair.json').write_text(json.dumps(row,indent=2)+'\n')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_uv_master.blend'),compress=True)
print('Exact shell repair',row,flush=True)
