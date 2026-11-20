"""Unwrap only the head in an isolated mesh, then transfer exact corner UVs to the animated master."""
import bpy,bmesh,math,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));body=bpy.data.objects['Body'];me=body.data
o=body.copy();o.data=me.copy();o.parent=None;o.modifiers.clear();o.vertex_groups.clear();bpy.context.collection.objects.link(o)
for name,domain,count in [('original_face','FACE',len(o.data.polygons)),('original_vertex','POINT',len(o.data.vertices))]:
 a=o.data.attributes.new(name,'INT',domain);a.data.foreach_set('value',list(range(count)))
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=1],context='FACES');bm.to_mesh(o.data);bm.free()
for ob in bpy.context.scene.objects:ob.select_set(ob==o)
bpy.context.view_layer.objects.active=o;bpy.context.scene.tool_settings.use_uv_select_sync=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(45),island_margin=0.,area_weight=0.,scale_to_bounds=False);bpy.ops.uv.pack_islands(margin=.0035,margin_method='FRACTION',rotate=True,shape_method='CONCAVE');bpy.ops.object.mode_set(mode='OBJECT')
uv=o.data.uv_layers.active.data;dst=me.uv_layers.active.data
for f in o.data.polygons:
 target=me.polygons[o.data.attributes['original_face'].data[f.index].value]
 corners={o.data.attributes['original_vertex'].data[v].value:uv[l].uv.copy() for v,l in zip(f.vertices,f.loop_indices)}
 for v,l in zip(target.vertices,target.loop_indices):dst[l].uv=corners[v]
o.data.materials.clear();m=bpy.data.materials.new('NeutralHead');m.use_nodes=True;o.data.materials.append(m)
for f in o.data.polygons:f.material_index=0
bpy.ops.export_scene.gltf(filepath=str(P/'work/head_upload.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False)
bpy.data.objects.remove(o,do_unlink=True);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_uv.blend'))
runpy.run_path(str(P/'scripts/check_head_uv.py'),run_name='__main__')
