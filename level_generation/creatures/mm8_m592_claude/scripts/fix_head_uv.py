"""Unwrap the isolated head, then return its per-corner UVs to the unchanged animated body."""
from pathlib import Path
import bpy,bmesh,json,numpy as np
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_reduced.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
me=body.data;bm=bmesh.new();bm.from_mesh(me);zero_faces=[f for f in bm.faces if f.calc_area()<1e-12];removed=len(zero_faces);bmesh.ops.delete(bm,geom=zero_faces,context='FACES_ONLY');bm.to_mesh(me);bm.free();print('REMOVED_ZERO_AREA_FACES',removed,flush=True);tag=me.attributes.get('source_face') or me.attributes.new('source_face','INT','FACE');tag.data.foreach_set('value',list(range(len(me.polygons))));up=body.copy();up.data=body.data.copy();bpy.context.collection.objects.link(up);up.parent=None;up.modifiers.clear();up.vertex_groups.clear();bm=bmesh.new();bm.from_mesh(up.data);hd=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if not f[hd]],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(up.data);bm.free()
for uv in list(up.data.uv_layers):up.data.uv_layers.remove(uv)
up.data.uv_layers.new(name='UVMap')
for ob in bpy.context.view_layer.objects:ob.select_set(ob==up)
bpy.context.view_layer.objects.active=up;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1,island_margin=.003,area_weight=.1,scale_to_bounds=False);bpy.ops.uv.pack_islands(margin=.003,rotate=True);bpy.ops.object.mode_set(mode='OBJECT')
areas=[];zero=[]
for f in up.data.polygons:
 vals=[up.data.uv_layers.active.data[i].uv.copy() for i in f.loop_indices];a,b,c=vals;area=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5;areas.append(area)
 if area<1e-12:zero.append({'face':f.index,'geometry_area':f.area,'uv_area':area})
print('ISOLATED_HEAD_UV',sum(areas),zero,flush=True)
assert .35<sum(areas)<1 and not zero,(sum(areas),zero)
for f in up.data.polygons:
 source=me.polygons[up.data.attributes['source_face'].data[f.index].value]
 for li,vi in zip(f.loop_indices,f.vertices):
  v=up.data.vertices[vi].co;target=min(source.loop_indices,key=lambda i:(me.vertices[me.loops[i].vertex_index].co-v).length);assert (me.vertices[me.loops[target].vertex_index].co-v).length<1e-6;me.uv_layers['HeadUV'].data[target].uv=up.data.uv_layers.active.data[li].uv
up.data.materials.clear();mat=bpy.data.materials.new('Neutral head');mat.use_nodes=True;up.data.materials.append(mat)
for f in up.data.polygons:f.material_index=0
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/m592_head_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False)
bpy.data.objects.remove(up,do_unlink=True);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_reduced.blend'));(P/'review/head_uv_pack.json').write_text(json.dumps({'head_triangles':len(areas),'summed_head_uv_area':sum(areas),'zero_uv_triangles':0,'zero_area_faces_removed':removed,'method':'Isolated head unwrap copied per corner to retained master'},indent=2)+'\n')
