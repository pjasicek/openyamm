"""Rebake onto the final fitted LOD0; all four LODs retain one texture set."""
import bpy,sys
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];T=P/'textures/round4_staff';W=P/'work/round4'
bpy.ops.wm.open_mainfile(filepath=str(P/'source/mm6_jak1_staff.blend'))
high=bpy.data.objects['AcceptedStaff'];low=bpy.data.objects['Staff'];source=high.data.materials[0];mat=low.data.materials[0]
high.hide_set(False);high.hide_render=False
nt=source.node_tree;bs=nt.nodes.get('Principled BSDF');output=nt.nodes.get('Material Output')
images={key:next(n for n in nt.nodes if n.type=='TEX_IMAGE'and n.image and f'accepted_{key}'in n.image.name)for key in ['basecolor','metal_rough','normal']}
for n in list(mat.node_tree.nodes):
 if n.type not in ['BSDF_PRINCIPLED','OUTPUT_MATERIAL']:mat.node_tree.nodes.remove(n)
recipe=(P/'scripts/round4_staff.py').read_text();exec(recipe[recipe.index('scene = bpy.context.scene;'):recipe.index('counts=[]')])
for level in range(4):
 obj=bpy.data.objects['Staff'if level==0 else f'Staff_LOD{level}']
 for other in bpy.context.scene.objects:other.select_set(other==obj)
 bpy.context.view_layer.objects.active=obj
 bpy.ops.export_scene.gltf(filepath=str(W/f'staff_lod{level}.glb'),use_selection=True,export_format='GLB',export_yup=False,export_animations=False,export_skins=False,export_morph=False,export_attributes=False)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/mm6_jak1_staff.blend'))
