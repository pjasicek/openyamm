"""Stage H: export the authoring master to a portable GLB (skin A material, all clips, palm sockets)."""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
out = os.path.join(common.PROJECT, 'export', 'mm6_gob_lod0.glb')
T = os.path.join(common.PROJECT, os.environ.get('TEXDIR', 'textures'))
mesh = bpy.data.objects['Peasant']; rig = bpy.data.objects['Peasant_Rig']
mat = bpy.data.materials.new('Peasant_A'); mat.use_nodes = True; mat.use_backface_culling = False
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
def tex(name, cs):
    img = bpy.data.images.load(os.path.join(T, name)); img.colorspace_settings.name = cs
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
# 1K body base colour: the face has its own head set.
bc = tex('gob_a_basecolor_graded_1k.png', 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
nm = tex('gob_normal_1k.png', 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = 1.0
nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex('gob_metal_rough_1k.png', 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
mesh.data.materials.clear(); mesh.data.materials.append(mat)
# Head texture set (scripts/head_split.py, compose_head.py): faces with the `head` attribute use GoblinHead_A.
head = bpy.data.materials.new('GoblinHead_A'); head.use_nodes = True; head.use_backface_culling = False
nt = head.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
bc = tex('gob_head_basecolor_graded.png', 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
nm = tex('gob_head_normal_1k.png', 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
mr = tex('gob_head_metal_rough_1k.png', 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
mesh.data.materials.append(head)
head_flags = [0] * len(mesh.data.polygons)
mesh.data.attributes['head'].data.foreach_get('value', head_flags)
mesh.data.polygons.foreach_set('material_index', head_flags)
if 'part' in mesh.data.attributes:
    pass  # kept in the master; the exporter skips custom attributes when export_attributes=False
# Walk stride from the planted-foot travel in the in-place gait (stance ~60% of the cycle).
act = bpy.data.actions['Walking']; rig.animation_data.action = act
ys = []
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
    bpy.context.scene.frame_set(f)
    ys.append((rig.matrix_world @ rig.pose.bones['mixamorig:LeftFoot'].head).y)
foot_range = max(ys) - min(ys)
stride = foot_range / 0.6
rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(1)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig) or o.name.startswith('Socket_'))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
lo, hi = common.world_bounds([mesh])
info = {'glb': out, 'stride_length_m': stride, 'foot_range_m': foot_range, 'rest_bounds_m': [list(lo), list(hi)]}
json.dump(info, open(os.path.join(common.PROJECT, 'export', 'export_info.json'), 'w'), indent=2)
print('EXPORTED', json.dumps(info))
