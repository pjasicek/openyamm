"""Export the drone master (work/anim_v1.blend, every clip) to export/hes_drone_lod0.glb.
Materials: Casing_A (parts 0-3, 5, 7: body, tendons, emitter barrel, ring band; base 2K, normal 1K, ORM 1K),
Glow_A (parts 4, 6, 8 and mat 5: lens dome, emitter disc, ring cells, vent slots and nozzle; same images, unlit after fix_materials.py),
Thrust_A on mesh node HDR_Thrust (alpha-blended gradient, unlit, double-sided)."""
import bpy, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
mesh = bpy.data.objects['HDR']; rig = bpy.data.objects['HDR_Rig']; thr = bpy.data.objects['HDR_Thrust']


def material(name, base, normal=None, mr=None, alpha=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(fn, cs):
        img = bpy.data.images.load(os.path.join(T, fn)); img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
    bc = tex(base, 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
    if alpha:
        nt.links.new(bc.outputs['Alpha'], bsdf.inputs['Alpha'])
        m.surface_render_method = 'BLENDED'; m.use_backface_culling = False
    if normal:
        nm = tex(normal, 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    if mr:
        t = tex(mr, 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(t.outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return m


casing = material('Casing_A', 'hdr_basecolor_2k.png', 'hdr_normal_1k.png', 'hdr_metal_rough_1k.png')
glow = material('Glow_A', 'hdr_basecolor_2k.png', 'hdr_normal_1k.png', 'hdr_metal_rough_1k.png')
thrust = material('Thrust_A', 'hdr_thrust.png', alpha=True)
mesh.data.materials.clear(); mesh.data.materials.append(casing); mesh.data.materials.append(glow)
pa = np.zeros(len(mesh.data.polygons), int); mesh.data.attributes['part'].data.foreach_get('value', pa)
ma = np.zeros(len(mesh.data.polygons), int)
if 'mat' in mesh.data.attributes:
    mesh.data.attributes['mat'].data.foreach_get('value', ma)
    mesh.data.attributes.remove(mesh.data.attributes['mat'])
glowing = np.isin(pa, (4, 6, 8)) | (ma == 5)                    # lens, gear glow, the vent slots and nozzle
mesh.data.polygons.foreach_set('material_index', glowing.astype(int).tolist())
mesh.data.attributes.remove(mesh.data.attributes['part'])
if 'TileUV' in mesh.data.uv_layers:
    mesh.data.uv_layers.remove(mesh.data.uv_layers['TileUV'])
mesh.data.uv_layers.active = mesh.data.uv_layers['UVMap']
thr.data.materials.clear(); thr.data.materials.append(thrust)
rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(1)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig, thr))
bpy.context.view_layer.objects.active = rig
out = os.path.join(HERE, 'export', 'hes_drone_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out)
