"""Export the hydra master (all clips) to export/mm6_hyd_lod0.glb: five materials over two texture sets (compose_hyd.py):
'Hydra', 'HydraB' (body texture: hyd_body_*) and 'HeadsA', 'HeadsB', 'HeadsC' (head texture: hyd_head_*), per face
from work/face_material.npy. Tiers are added afterwards by claude_shared/region_variants.py."""
import bpy, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
MATERIALS = [('Hydra', 'body'), ('HydraB', 'body'), ('HeadsA', 'head'), ('HeadsB', 'head'), ('HeadsC', 'head')]
mesh = bpy.data.objects['Hydra']; rig = bpy.data.objects['Hydra_Rig']; me = mesh.data
face_mat = np.load(os.path.join(HERE, 'work', 'face_material.npy'))
assert len(face_mat) == len(me.polygons), 'face_material.npy is for another mesh'
images = {}


def material(name, tex):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; mat.use_backface_culling = False; nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def node(file, cs):
        if file not in images:
            images[file] = bpy.data.images.load(os.path.join(T, file)); images[file].colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = images[file]; return n

    nt.links.new(node(f'hyd_{tex}_basecolor_graded.png', 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(node(f'hyd_{tex}_normal.png', 'Non-Color').outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(node(f'hyd_{tex}_metal_rough.png', 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


me.materials.clear()
for name, tex in MATERIALS:
    me.materials.append(material(name, tex))
me.polygons.foreach_set('material_index', face_mat.astype(np.int32))
for a in [a for a in me.attributes if a.name in ('part', 'graft_src', 'head_skull', 'chain_owner', 'loft_s', 'loft_ref')]:
    me.attributes.remove(a)
me.update()
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(0)
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
out = os.path.join(HERE, 'export', 'mm6_hyd_lod0.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True)
print('EXPORTED', out, 'faces per material', np.bincount(face_mat, minlength=5).tolist())
