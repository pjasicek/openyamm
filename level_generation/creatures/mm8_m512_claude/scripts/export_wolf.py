"""Apply the verified maps to the retained rig, pack an editable master and export the eight clips."""
import bpy
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1];T=PROJECT/'textures'
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/wolf_uv_settled.blend'))
mesh=bpy.data.objects['Wolf'];rig=bpy.data.objects['Wolf_Rig'];sc=bpy.context.scene
# glTF omits influences below 0.0001; keep the editable master on that same weight set.
for vertex in mesh.data.vertices:
    for group in list(vertex.groups):
        if group.weight<.0001:mesh.vertex_groups[group.group].remove([vertex.index])
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
bpy.ops.object.vertex_group_normalize_all(lock_active=False)

mat=bpy.data.materials.new('Wolf');mat.use_nodes=True;mat['openyamm_specular']=0.0
nodes=mat.node_tree.nodes;links=mat.node_tree.links;bsdf=nodes.get('Principled BSDF')
bsdf.inputs['Metallic'].default_value=0;bsdf.inputs['Specular IOR Level'].default_value=0
def texture(name,space):
    node=nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(T/name))
    node.image.colorspace_settings.name=space;return node
base=texture('wolf_basecolor.png','sRGB');links.new(base.outputs['Color'],bsdf.inputs['Base Color'])
normal=texture('wolf_normal_1k.png','Non-Color');n=nodes.new('ShaderNodeNormalMap')
links.new(normal.outputs['Color'],n.inputs['Color']);links.new(n.outputs['Normal'],bsdf.inputs['Normal'])
mr=texture('wolf_metal_rough_1k.png','Non-Color');sep=nodes.new('ShaderNodeSeparateColor')
links.new(mr.outputs['Color'],sep.inputs['Color']);links.new(sep.outputs['Green'],bsdf.inputs['Roughness'])
mesh.data.materials.clear();mesh.data.materials.append(mat)
for face in mesh.data.polygons:face.material_index=0
# The portable clip uses linear samples; use the same interpolation in the editable master.
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);rig.select_set(True)
bpy.context.view_layer.objects.active=rig
def export(name):
    bpy.ops.export_scene.gltf(filepath=str(PROJECT/'export'/name),use_selection=True,
        export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',
        export_force_sampling=True,export_skins=True,export_all_influences=False,export_morph=False,
        export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
export('wolf_lod0_raw.glb')
base.image=bpy.data.images.load(str(T/'wolf_preview_a.png'))
export('wolf_viewer.glb')
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'export/mm8_wolf.blend'))
assert len([a for a in bpy.data.actions if a.name in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']])==8
