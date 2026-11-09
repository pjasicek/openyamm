"""Export the retained animated rig with its transferred atlas; join only the runtime draw mesh."""
import bpy,sys,os,signal
from pathlib import Path
signal.alarm(900)
P=Path(__file__).resolve().parents[1];T=P/'textures'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
mat=bpy.data.materials.new('BroodMotherSurface');mat.use_nodes=True;mat.use_backface_culling=True
nt=mat.node_tree;bsdf=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
def tex(name,space):
 n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/name));n.image.colorspace_settings.name=space;return n
nt.links.new(tex('hbm_basecolor.png','sRGB').outputs['Color'],bsdf.inputs['Base Color'])
nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('hbm_normal.png','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('hbm_metal_rough.png','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bsdf.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
mat['openyamm_specular_mask']=True
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in meshes:
 o.data.materials.clear();o.data.materials.append(mat)
 for f in o.data.polygons:f.material_index=0
 for a in list(o.data.color_attributes):o.data.color_attributes.remove(a)
for im in bpy.data.images:
 if im.source=='FILE':im.pack()
(P/'export').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/hes_brood_mother.blend'))
for o in bpy.context.scene.objects:o.select_set(o in meshes)
bpy.context.view_layer.objects.active=bpy.data.objects['BroodMother'];bpy.ops.object.join()
body=bpy.context.object;body.name='BroodMother'
# Joins can retain duplicate slots although every piece uses the same atlas.
body.data.materials.clear();body.data.materials.append(mat)
for f in body.data.polygons:f.material_index=0
for o in bpy.context.scene.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
rig.animation_data.action=bpy.data.actions['Standing']
if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(0)
bpy.ops.export_scene.gltf(filepath=str(P/'work/runtime_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,
 export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,
 export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
