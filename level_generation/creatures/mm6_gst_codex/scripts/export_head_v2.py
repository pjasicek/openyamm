import bpy,bmesh
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];o=body.copy();o.data=body.data.copy();o.parent=None;o.modifiers.clear();o.vertex_groups.clear();bpy.context.collection.objects.link(o);bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=1],context='FACES');bm.to_mesh(o.data);bm.free();o.data.materials.clear();m=bpy.data.materials.new('Neutral');m.use_nodes=True;o.data.materials.append(m)
for f in o.data.polygons:f.material_index=0
for ob in bpy.context.scene.objects:ob.select_set(ob==o)
bpy.context.view_layer.objects.active=o;bpy.ops.export_scene.gltf(filepath=str(P/'work/head_upload_v2.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False)
