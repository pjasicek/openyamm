"""Export the mantis master (material Mantis_A on the graded shared paint, every clip at 30 fps) to
export/xeen_mantis_lod0.glb. Args: -- [out.glb]"""
import bpy, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out = os.path.join(HERE, a[0]) if a else os.path.join(HERE, 'export', 'xeen_mantis_lod0.glb')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
mesh = bpy.data.objects['Mantis']; rig = bpy.data.objects['Mantis_Rig']


def material(name, color, normal=None, mr=None, rough=None):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(path, cs):
        img = bpy.data.images.load(path, check_existing=False); img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
    bc = tex(color, 'sRGB'); nt.links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])
    if normal:
        nm = tex(normal, 'Non-Color'); nmap = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    if mr:
        m = tex(mr, 'Non-Color'); sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(m.outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    else:
        bsdf.inputs['Roughness'].default_value = rough; bsdf.inputs['Metallic'].default_value = 0.0
    return mat


mesh.data.materials.clear()
mesh.data.materials.append(material('Mantis_A', os.path.join(T, 'mantis_basecolor_graded.png'),
                                    os.path.join(T, 'mantis_normal_1k.png'), os.path.join(T, 'mantis_mr_1k.png')))
sc = bpy.context.scene
sc.render.fps = 30; sc.render.fps_base = 1
rig.animation_data.action = bpy.data.actions['Standing']
if len(getattr(bpy.data.actions['Standing'], 'slots', [])):
    rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
sc.frame_set(0)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True, export_def_bones=False)
print('EXPORTED', out)
