import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3'
for row in json.loads((P/'review/round3/lod_selection.json').read_text()):
 lod=row['lod'];bpy.ops.wm.open_mainfile(filepath=str(P/row['blend']));body=bpy.data.objects['Body'];body.hide_render=False;body.hide_viewport=False;body.hide_set(False);rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.wm.save_as_mainfile(filepath=str(W/f'rebaked_l{lod}.blend'));bpy.ops.export_scene.gltf(filepath=str(W/f'geometry_body_l{lod}.glb'),use_selection=True,export_format='GLB',export_animations=False,export_all_influences=True,export_attributes=False)
