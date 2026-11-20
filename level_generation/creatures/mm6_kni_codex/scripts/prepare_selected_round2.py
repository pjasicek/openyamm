import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduce_round2 as red
W=P/'work/round2';rows=json.loads((P/'review/round2/selection.json').read_text())
for row in rows:
 part,level=row['part'],row['lod'];tag=f'{part}_l{level}'
 if row.get('unchanged'):
  if part=='body':body,rig=red.reset(level)
  else:
   bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(W/f'baseline_sword_l{level}.glb'));body=bpy.data.objects['Sword'];rig=None
 else:
  bpy.ops.wm.open_mainfile(filepath=str(P/row['blend']));body=bpy.data.objects['Body'if part=='body'else 'Sword'];rig=bpy.data.objects.get('Rig')
 if rig:
  rig.animation_data.action=None
  for pb in rig.pose.bones:pb.matrix_basis.identity()
  bpy.context.view_layer.update()
 for o in bpy.data.objects:o.select_set(o in [body,rig])
 bpy.context.view_layer.objects.active=body
 bpy.ops.wm.save_as_mainfile(filepath=str(W/f'selected_{tag}.blend'))
 bpy.ops.export_scene.gltf(filepath=str(W/f'geometry_{tag}.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=bool(rig),export_all_influences=True,export_attributes=False,export_yup=True)
 print('SELECTED',tag,row['triangles'],flush=True)
