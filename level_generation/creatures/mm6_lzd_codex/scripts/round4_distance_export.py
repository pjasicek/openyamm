import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
selection=json.loads((P/'review/round4/lod_selection.json').read_text());meta=json.loads((P/'review/rebake/round4_shared_bake.json').read_text())
for level,path in [(2,'work/round4/lod2_contact_final.blend'),(3,'work/round4/round4_refine_0_0.001.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/path));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
 targets=[bpy.data.materials[meta[g]['material']]for g in ['body','head','bow']]
 old=list(body.data.materials);indices=[2 if 'Bow'in old[f.material_index].name else 1 if 'Head'in old[f.material_index].name else 0 for f in body.data.polygons]
 body.data.materials.clear()
 for m in targets:body.data.materials.append(m)
 for f,i in zip(body.data.polygons,indices):f.material_index=i
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(P/path))
 selection[str(level)]={'blend':path,'tag':'round4_contact_final'if level==2 else'round4_refine_0_0.001','method':'Near shared UVs; quiver silhouettes restored; constrained multi-view vertex fitting; grip/sole constraints retained.'}
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig;body.name=body.data.name='Lizard'
 bpy.ops.export_scene.gltf(filepath=str(P/f'export/mm6_lzd_level{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO')
(P/'review/round4/lod_selection.json').write_text(json.dumps(selection,indent=2))
