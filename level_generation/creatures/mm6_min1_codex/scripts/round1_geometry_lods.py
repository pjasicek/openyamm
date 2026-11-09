"""Export the selected native lower meshes in the identical skin bind space."""
import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_materials as M
for level in range(1,4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round1_lod{level}.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();M.setup(b,ax,directory=P/'textures/round1_rebaked',rebaked=True)
 bpy.ops.object.select_all(action='DESELECT');b.select_set(True);ax.select_set(True);bpy.context.view_layer.objects.active=b;bpy.ops.object.join();b.name=b.data.name='Minotaur'
 for n in ['piece','finger','head','orig_co']:
  if n in b.data.attributes:b.data.attributes.remove(b.data.attributes[n])
 bpy.ops.object.select_all(action='DESELECT');b.select_set(True);r.select_set(True);bpy.context.view_layer.objects.active=r
 bpy.ops.export_scene.gltf(filepath=str(P/f'export/mm6_min1_geometry_lod{level}.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO')
