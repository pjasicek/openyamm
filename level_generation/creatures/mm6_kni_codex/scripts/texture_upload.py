"""Rest-pose reduced body upload; Meshy owns the new unwrap. Helmet is sealed, not a visible human face."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_body.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();body.data.attributes.new('head','INT','FACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/production_body.blend'))
ob=bpy.data.objects.new('KnightPlate',body.data.copy());bpy.context.scene.collection.objects.link(ob)
for o in bpy.data.objects:o.select_set(o==ob)
bpy.context.view_layer.objects.active=ob
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_retexture.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False)
assert len(ob.data.vertices)>5000
print('UPLOAD',len(ob.data.vertices),'vertices',len(ob.data.polygons),'faces')
