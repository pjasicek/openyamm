"""Export work/uv_r1.blend (reduce_lod0.py 0.45 0.7 0.5 0.5 of uv_master): body material Dragonfly_A (shared tier
skin) and the four wings split into their own mesh node DragonflyWings with an alpha-blended, double-sided material
DragonflyWing_A (same base colour atlas, alpha WING_ALPHA), as the native see-through wings.
Writes export/mm7_m186_lod0.glb and work/m186_textured_master.blend."""
from pathlib import Path
import sys
import bpy, bmesh
P = Path(__file__).resolve().parents[1]
# optional: <blend> <out glb> <master blend> relative to the project (the unreduced reduction source uses work/uv_full.blend)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SRC, OUT, MASTER = (ARGS + ['work/uv_r1.blend', 'export/mm7_m186_lod0.glb', 'work/m186_textured_master.blend'][len(ARGS):])[:3]
WING_ALPHA = 0.62
bpy.ops.wm.open_mainfile(filepath=str(P / SRC))
mesh = bpy.data.objects['Dragonfly']; rig = bpy.data.objects['Dragonfly_Rig']
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
def images():
    out = {}
    for name, space in (('dfly_basecolor.png', 'sRGB'), ('dfly_normal.png', 'Non-Color'), ('dfly_metal_rough.png', 'Non-Color')):
        img = bpy.data.images.load(str(P / 'textures' / name)); img.colorspace_settings.name = space; img.pack(); out[name] = img
    return out
IMG = images()
def material(name, wing):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; mat.use_backface_culling = False
    nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    def tex(key):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = IMG[key]; return n
    nt.links.new(tex('dfly_basecolor.png').outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex('dfly_normal.png').outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    if wing:
        bsdf.inputs['Alpha'].default_value = WING_ALPHA; bsdf.inputs['Roughness'].default_value = 0.35
        bsdf.inputs['Metallic'].default_value = 0.0
        mat.surface_render_method = 'BLENDED'
        mat['openyamm_specular'] = 0.5
    else:
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex('dfly_metal_rough.png').outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
        mat['openyamm_specular'] = 1.0; mat['openyamm_specular_mask'] = True
    return mat
mesh.data.materials.clear()
mesh.data.materials.append(material('Dragonfly_A', False)); mesh.data.materials.append(material('DragonflyWing_A', True))
wing_groups = {mesh.vertex_groups[n].index for n in ('ForeWing_L', 'ForeWing_R', 'HindWing_L', 'HindWing_R')}
for p in mesh.data.polygons:
    vs = [mesh.data.vertices[i] for i in p.vertices]
    p.material_index = 1 if all(any(g.group in wing_groups and g.weight > .5 for g in v.groups) for v in vs) else 0
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects: o.select_set(o == mesh)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT')
mesh.active_material_index = 1; bpy.ops.object.material_slot_select(); bpy.ops.mesh.separate(type='SELECTED')
bpy.ops.object.mode_set(mode='OBJECT')
wings = next(o for o in bpy.data.objects if o.type == 'MESH' and o is not mesh)
wings.name = wings.data.name = 'DragonflyWings'
for o, keep in ((mesh, 'Dragonfly_A'), (wings, 'DragonflyWing_A')):
    for i in reversed(range(len(o.data.materials))):
        if o.data.materials[i].name != keep:
            o.data.materials.pop(index=i)
rig.animation_data.action = bpy.data.actions['Fly']; bpy.context.scene.frame_set(1)
for o in bpy.context.scene.objects: o.select_set(o in (mesh, wings, rig))
bpy.context.view_layer.objects.active = rig
(P / 'export').mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P / MASTER))
bpy.ops.export_scene.gltf(filepath=str(P / OUT), use_selection=True, export_format='GLB',
    export_yup=True, export_animations=True, export_animation_mode='ACTIONS', export_frame_range=False,
    export_force_sampling=True, export_frame_step=1, export_skins=True, export_all_influences=False,
    export_attributes=False, export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
    export_anim_slide_to_zero=True, export_extras=True)
print('EXPORTED', len(mesh.data.polygons), 'body,', len(wings.data.polygons), 'wing faces;', sorted(a.name for a in bpy.data.actions))
