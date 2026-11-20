"""Keep an independently editable, textured head alongside the merged runtime creature."""
from pathlib import Path
import bpy,bmesh
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm8_m620.blend'))
body=bpy.data.objects['Bedraggled'];bm=bmesh.new();bm.from_mesh(body.data)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index==0],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(body.data);bm.free();body.name='BedraggledHead'
assert len(body.data.polygons)>4000
for o in bpy.data.objects:o.select_set(o.type in ('MESH','ARMATURE'))
bpy.context.view_layer.objects.active=bpy.data.objects['Rig']
bpy.ops.export_scene.gltf(filepath=str(p/'export/mm8_m620_head.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(p/'export/mm8_m620_head.blend'))
