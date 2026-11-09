import bpy,bmesh,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/repaired_geometry.blend'));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
for slot,label in [(0,'body'),(2,'wings')]:
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
 for f in o.data.polygons:f.select=f.material_index==slot
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.003);bpy.ops.uv.pack_islands(rotate=True,margin=.003,margin_method='FRACTION');bpy.ops.object.mode_set(mode='OBJECT')
 dup=o.copy();dup.data=o.data.copy();dup.parent=None;dup.modifiers.clear();dup.vertex_groups.clear();bpy.context.collection.objects.link(dup);bm=bmesh.new();bm.from_mesh(dup.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=slot],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(dup.data);bm.free();dup.data.materials.clear();mat=bpy.data.materials.new('Neutral');mat.use_nodes=True;dup.data.materials.append(mat)
 for f in dup.data.polygons:f.material_index=0
 bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
 bpy.ops.export_scene.gltf(filepath=str(P/f'work/{label}_upload_v2.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False);bpy.data.objects.remove(dup,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/repair_uv.blend'))
