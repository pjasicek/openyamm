"""Full silhouette body upload; Meshy unwraps it, while our separate head set stays selected."""
import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
body.parent=None;body.modifiers.clear();body.vertex_groups.clear();body.data.materials.clear();m=bpy.data.materials.new('Neutral');m.use_nodes=True;body.data.materials.append(m)
for f in body.data.polygons:f.material_index=0
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/med_body_full_upload_v2.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False,export_morph=False)
print('FULL BODY UPLOAD',len(body.data.polygons))
