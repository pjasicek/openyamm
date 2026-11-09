"""Apply the audited Meshy maps to the authored parts without replacing geometry or rigging."""
import json

import bpy
from mathutils import Vector

from mesh_tools import ROOT
import motion
import export_asset

TEXTURES = ROOT / 'textures/meshy_20260928'
REVIEW = ROOT / 'review/texturing_20260928'


def apply():
    audit = json.loads((TEXTURES / 'import_audit.json').read_text())
    assert audit['status'] == 'pass' and audit['uvs_bit_identical']
    source = bpy.data.scenes['MM6 Goblin - Authored 15K']
    assert source.get('gb_owner') == str(ROOT)
    assert not source.get('gb_meshy_texture_revision'), 'Material revision is already applied.'
    imported = bpy.data.scenes['GB15 Meshy return inspection']
    obj = next(o for o in imported.objects if o.type == 'MESH')
    template = obj.data.materials[0]
    principled = next(n for n in template.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    base = principled.inputs['Base Color'].links[0].from_node.image
    separate = principled.inputs['Roughness'].links[0].from_node
    packed = separate.inputs[0].links[0].from_node.image
    normal_node = principled.inputs['Normal'].links[0].from_node
    normal = normal_node.inputs['Color'].links[0].from_node.image
    for image, role in [(base, 'base_color'), (packed, 'metallic_roughness'), (normal, 'normal')]:
        image.name = 'GB15 Meshy ' + role
        image.filepath = str(TEXTURES / (role + '.jpg'))
        if not image.packed_file:
            image.pack()
    assert base.colorspace_settings.name == 'sRGB'
    assert packed.colorspace_settings.name == normal.colorspace_settings.name == 'Non-Color'
    assignment, replacements = {}, {}
    for obj in bpy.data.collections['GB15 Character'].objects:
        if obj.type != 'MESH':
            continue
        assignment[obj.name] = [material.name for material in obj.data.materials]
        for i, original in enumerate(list(obj.data.materials)):
            if original.name not in replacements:
                original.use_fake_user = True
                material = template.copy()
                material.name = original.name.replace('GB15 ', 'GB15 Meshy ').replace(' blockout', '')
                material['gb_texture_revision'] = 'meshy_20260928'
                material['gb_original_material'] = original.name
                material['gb_texture_source_sha256'] = audit['source_sha256']
                replacements[original.name] = material
            obj.data.materials[i] = replacements[original.name]
    (TEXTURES / 'material_assignment.json').write_text(json.dumps({
        'original_slots': assignment,
        'new_materials': {name: material.name for name, material in replacements.items()},
        'normal_choice': 'Returned Meshy tangent normal at strength 1; prior source proof retained separately.',
        'maps_modified': False}, indent=2) + '\n')
    source['gb_meshy_texture_revision'] = 'meshy_20260928'
    bpy.context.window.scene = source
    motion.activate('standing')
    for obj in list(imported.objects):
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data.users == 0:
            bpy.data.meshes.remove(data)
    bpy.data.scenes.remove(imported)
    if template.users == 0:
        bpy.data.materials.remove(template)
    REVIEW.mkdir(parents=True, exist_ok=True)
    print('Applied three shared PBR maps across', len(replacements), 'retained material regions.')


def export():
    scene = bpy.data.scenes['MM6 Goblin - Authored 15K']
    bpy.context.window.scene = scene
    assert scene.get('gb_meshy_texture_revision') == 'meshy_20260928'
    motion.activate('standing')
    objects = list(bpy.data.collections['GB15 Character'].objects)
    export_asset.selected(objects)
    bpy.ops.export_scene.gltf(filepath=str(ROOT / 'delivery/mm6_goblin_textured_rigged.glb'),
        export_format='GLB', use_selection=True, use_active_scene=True, export_apply=True, export_texcoords=True,
        export_normals=True, export_tangents=True, export_materials='EXPORT', export_all_vertex_colors=False,
        export_yup=True, export_extras=True, export_skins=True, export_influence_nb=4, export_all_influences=False,
        export_animations=True, export_animation_mode='ACTIONS', export_rest_position_armature=True,
        export_frame_range=False, export_force_sampling=True, export_frame_step=1, export_anim_single_armature=True)
    export_asset.selected([bpy.data.objects['GB15 Goblin rig']])
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'delivery/mm6_goblin_textured.blend'), compress=True)
    print('Saved separate textured Blender and rigged GLB deliveries.')


def first_look():
    """Two short renders before committing to the longer portable-asset review."""
    scene = bpy.context.scene
    camera = scene.camera
    queue = [('quarter', (-3, -5, 2.2), (0, 0, .87), 1.99),
             ('head', (-.20, -3, 1.585), (0, 0, 1.56), .42)]
    def step():
        if not queue:
            return None
        name, position, target, scale = queue.pop(0)
        camera.location = position
        camera.rotation_euler = (Vector(target)-camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.ortho_scale = scale
        bpy.data.objects['GB15 Ground'].hide_render = name == 'head'
        scene.render.resolution_x = 960
        scene.render.resolution_y = 1120 if name == 'quarter' else 960
        scene.render.filepath = str(REVIEW / ('source_' + name + '.png'))
        bpy.ops.render.render(write_still=True)
        return .1
    bpy.app.timers.register(step, first_interval=.1)
    print('Scheduled two initial material renders.')


def compare_normals_and_eyes():
    """Render small material alternatives; restore the incoming Meshy materials after each render."""
    scene = bpy.context.scene
    skin = bpy.data.materials['GB15 Meshy Skin']
    normal_texture = next(n for n in skin.node_tree.nodes if n.type == 'TEX_IMAGE' and
                          n.image.name == 'GB15 Meshy normal')
    incoming = normal_texture.image
    old = bpy.data.materials['GB15 Skin blockout']
    source_normal = next(n.image for n in old.node_tree.nodes if n.type == 'TEX_IMAGE')
    eye_objects = [bpy.data.objects[name] for name in ['GB15 Eyes', 'GB15 Irises', 'GB15 Pupils']]
    textured = [obj.data.materials[0] for obj in eye_objects]
    originals = [bpy.data.materials[name] for name in ['GB15 Eyes', 'GB15 Amber irises', 'GB15 Pupils']]
    queue = [('head_source_normal', True, False), ('head_original_eyes', False, True),
             ('head_source_normal_original_eyes', True, True)]
    def step():
        if not queue:
            (REVIEW / 'material_comparison_status.json').write_text('{"state":"complete"}')
            return None
        name, use_source, use_eyes = queue.pop(0)
        try:
            normal_texture.image = source_normal if use_source else incoming
            for obj, material in zip(eye_objects, originals if use_eyes else textured):
                obj.data.materials[0] = material
            scene.render.filepath = str(REVIEW / (name + '.png'))
            bpy.ops.render.render(write_still=True)
        finally:
            normal_texture.image = incoming
            for obj, material in zip(eye_objects, textured):
                obj.data.materials[0] = material
        return .1
    bpy.app.timers.register(step, first_interval=.1)
    print('Scheduled three normal/eye comparison renders.')
