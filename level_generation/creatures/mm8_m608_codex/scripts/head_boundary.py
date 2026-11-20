"""Move the head texture boundary below the chin; preserve body UVs and fitted weights."""
import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.geometry import closest_point_on_tri,barycentric_transform
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
body=bpy.data.objects['Body'];head=bpy.data.objects['Head'];body.data.calc_loop_triangles();old=body.data.copy();triangles=list(old.loop_triangles)
tree=KDTree(len(triangles))
for i,tr in enumerate(triangles):tree.insert(sum((old.vertices[v].co for v in tr.vertices),Vector())/3,i)
tree.balance();oldUV=old.uv_layers.active.data
for o,value in [(body,False),(head,True)]:
 a=o.data.attributes.new('old_head','BOOLEAN','FACE')
 for d in a.data:d.value=value
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);head.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
mesh=body.data;uv=mesh.uv_layers.active.data;count=0
for f in mesh.polygons:
 center=sum((mesh.vertices[i].co for i in f.vertices),Vector())/len(f.vertices)
 selected=abs(center.x+.012)<.122 and center.z>.773
 f.select=selected
 if mesh.attributes['old_head'].data[f.index].value and not selected:
  _,ti,_=tree.find(center);tr=triangles[ti];points=[old.vertices[i].co for i in tr.vertices];values=[Vector((*oldUV[i].uv,0)) for i in tr.loops]
  for li,vi in zip(f.loop_indices,f.vertices):
   point=closest_point_on_tri(mesh.vertices[vi].co,*points);uv[li].uv=barycentric_transform(point,*points,*values).xy
  a,b,c=[uv[i].uv for i in f.loop_indices]
  if abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))<1e-10:
   for li,value in zip(f.loop_indices,values):uv[li].uv=value.xy
  count+=1
bpy.context.tool_settings.mesh_select_mode=(False,False,True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT');head=next(o for o in bpy.context.selected_objects if o!=body);head.name='Head'
bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head
for layer in list(head.data.uv_layers):head.data.uv_layers.remove(layer)
head.data.uv_layers.new(name='UVMap');bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=.95,island_margin=.008);bpy.ops.uv.pack_islands(margin=.008,rotate=True);bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'))
dup=head.copy();dup.data=head.data.copy();dup.parent=None;dup.modifiers.clear();bpy.context.collection.objects.link(dup);bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/head_neutral_v2.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_materials='NONE')
(P/'work/head_boundary_v2.json').write_text(json.dumps({'head_triangles':len(head.data.polygons),'body_triangles':len(body.data.polygons),'shoulder_faces_reprojected_to_existing_body_uvs':count,'reason':'Original plane cut across the two long chin plates; new boundary follows the short stone neck.'},indent=2))
print('HEAD_BOUNDARY',len(head.data.polygons),count,flush=True)
