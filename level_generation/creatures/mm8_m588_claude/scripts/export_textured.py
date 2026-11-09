"""Apply verified maps to the retained animated rig, pack the master and export without retiming."""
import bpy,sys,json
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];T=P/'textures'
sys.path.insert(0,str(P.parent/'mm8_m584_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
body.data.materials.clear()
for old in list(bpy.data.materials):
 if old.users==0:bpy.data.materials.remove(old)
mat=bpy.data.materials.new('Boulder');mat.use_nodes=True
nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
def tex(filename,space):
 node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(T/filename));node.image.colorspace_settings.name=space;return node
base=tex('boulder_basecolor_2k.png','sRGB');nt.links.new(base.outputs['Color'],bs.inputs['Base Color']);nt.nodes.active=base
normal=tex('boulder_normal_1k.png','Non-Color');nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(normal.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
orm=tex('boulder_metal_rough_1k.png','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(orm.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
body.data.materials.clear();body.data.materials.append(mat)
for f in body.data.polygons:f.material_index=0
mat.name='Boulder';body.data.materials[0].name='Boulder'
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update();bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/boulder_master.blend'))
for ob in bpy.data.objects:ob.select_set(ob.type in ('MESH','ARMATURE','EMPTY'))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/boulder_portable.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_optimize_animation_size=False)
action=bpy.data.actions['Standing'];rig.animation_data.action=action
if action.slots:rig.animation_data.action_slot=action.slots[0]
sc.frame_set(0);common.workbench_clay(sc,textured=True)
common.render_views(str(P/'review/textured'),1,2.8,views=('front','left','back','three_quarter'),resolution=(900,900))
