"""Apply surgical material corrections in a new live Blender scene; preserve the UV master."""
import json
from pathlib import Path

import bpy

stage = Path(__file__).resolve().parent
SCENE = 'MM6_Demon_Textured_Animations'


def select(scene, clip, frame):
    bpy.context.window.scene = scene
    for obj in scene.objects:
        for owner in (obj, obj.data.shape_keys if obj.type == 'MESH' else None):
            if owner is not None and owner.animation_data:
                matches = [t.strips[0] for t in owner.animation_data.nla_tracks if t.name == clip]
                for track in owner.animation_data.nla_tracks:
                    track.mute = True
                owner.animation_data.action = matches[0].action if matches else None
                if matches:
                    owner.animation_data.action_slot = matches[0].action_slot
    scene.frame_set(int(frame), subframe=float(frame % 1))
    bpy.context.view_layer.update()


def srgb(rgb):
    return tuple(c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb)+(1.,)


def flat_material(name, rgb, roughness):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = srgb(rgb)
    bsdf.inputs['Metallic'].default_value = 0
    bsdf.inputs['Roughness'].default_value = roughness
    material.diffuse_color = srgb(rgb)
    return material


def apply():
    assert SCENE not in bpy.data.scenes, 'Material revision already exists; do not append a second revision.'
    with bpy.data.libraries.load(str(stage / 'uv_source_checkpoint.blend')) as (_, loaded):
        loaded.scenes = ['MM6_Demon_Native_Animations']
    scene = loaded.scenes[0]
    scene.name = SCENE
    scene['material_revision'] = 'Meshy return, white talons, salmon-red iris, black pupil'
    mesh = next(o for o in scene.objects if o.name.startswith('Demon_Native_Mesh'))
    rig = next(o for o in scene.objects if o.type == 'ARMATURE')
    # Names are unique in the GUI; the exporter later assigns canonical names in its isolated process.
    for obj in list(scene.objects):
        obj.name = 'Textured_' + obj.name.split('.')[0]
    mesh['material_role'] = 'body'
    rig['material_role'] = 'rig'
    imported_scene = bpy.data.scenes.new('MM6_Meshy_Material_Import')
    bpy.context.window.scene = imported_scene
    source_path = json.loads((stage / 'material_regions.json').read_text())['source_glb']
    bpy.ops.import_scene.gltf(filepath=source_path)
    returned = next(o for o in imported_scene.objects if o.type == 'MESH')
    body = returned.data.materials[0].copy()
    body.name = 'Demon_Meshy_Body'
    for node in body.node_tree.nodes:
        if node.type in ('UVMAP', 'NORMAL_MAP'):
            node.uv_map = 'Meshy_Atlas'
        if node.type == 'TEX_IMAGE' and node.image:
            node.image.pack()
    body_shader = next(n for n in body.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for link in list(body_shader.inputs['Metallic'].links):
        body.node_tree.links.remove(link)
    body_shader.inputs['Metallic'].default_value = 0
    iris = flat_material('Demon_Red_Iris', (.86, .38, .36), .22)
    pupil = flat_material('Demon_Black_Pupil', (.015, .012, .012), .18)
    claws = body.copy()
    claws.name = 'Demon_White_Claws'
    bsdf = next(n for n in claws.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for name, value in [('Base Color', srgb((.95, .95, .95))), ('Metallic', 0.)]:
        for link in list(bsdf.inputs[name].links):
            claws.node_tree.links.remove(link)
        bsdf.inputs[name].default_value = value
    # Retain generated roughness and tangent-normal detail on the talons.
    claws.diffuse_color = srgb((.95, .95, .95))
    assert len(mesh.data.materials) == 3
    for i, material in enumerate((body, iris, pupil)):
        mesh.data.materials[i] = material
    mesh.data.materials.append(claws)
    regions = json.loads((stage / 'material_regions.json').read_text())
    for index in regions['claw_faces']:
        polygon = mesh.data.polygons[index]
        assert polygon.material_index == 0
        polygon.material_index = 3
    for obj in list(imported_scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.scenes.remove(imported_scene)
    bpy.context.window.scene = scene
    bake_claw_colour(scene)
    select(scene, 'Standing', 0)
    scene.render.fps = 48
    scene.frame_start, scene.frame_end = 0, 6
    rig.hide_set(True)
    for obj in scene.objects:
        obj.select_set(False)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    finish(scene)
    print('Material correction authored:', scene.name, regions['hand_claw_faces'], 'hand talon faces,',
          regions['foot_claw_faces'], 'foot talon faces; separate red iris and black pupil.')


def finish(scene):
    mesh = next(o for o in scene.objects if o.get('material_role') == 'body')
    scene.render.engine = 'BLENDER_EEVEE'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                valid = [e.identifier for e in area.spaces.active.shading.bl_rna.properties['type'].enum_items]
                assert 'MATERIAL' in valid
                area.spaces.active.shading.type = 'MATERIAL'
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
    for image in {n.image for m in mesh.data.materials for n in m.node_tree.nodes
                  if n.type == 'TEX_IMAGE' and n.image}:
        image.pack()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'authored_checkpoint.blend'), compress=True)


def bake_claw_colour(scene):
    """Bake neutral keratin pigment, preserving dark root shading instead of hard white face edges."""
    mesh = next(o for o in scene.objects if o.get('material_role') == 'body')
    regions = json.loads((stage / 'material_regions.json').read_text())
    selected = [mesh.data.polygons[i] for i in regions['claw_faces']]
    scratch = bpy.data.scenes.new('MM6_Claw_Colour_Bake')
    bpy.context.window.scene = scratch
    scratch.render.engine = 'CYCLES'
    scratch.cycles.samples = 1
    data = bpy.data.meshes.new('MM6_Claw_Bake_Surface')
    data.from_pydata([tuple(v.co) for v in mesh.data.vertices], [], [tuple(p.vertices) for p in selected])
    uv = data.uv_layers.new(name='Meshy_Atlas')
    for old, new in zip(selected, data.polygons):
        for a, b in zip(old.loop_indices, new.loop_indices):
            uv.data[b].uv = mesh.data.uv_layers['Meshy_Atlas'].data[a].uv
    obj = bpy.data.objects.new('MM6_Claw_Bake_Surface', data)
    scratch.collection.objects.link(obj)
    material = mesh.data.materials[0].copy()
    material.name = 'MM6_Claw_Bake_Emission'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    pigment = bsdf.inputs['Base Color'].links[0].from_socket
    gray = nodes.new('ShaderNodeRGBToBW')
    links.new(pigment, gray.inputs['Color'])
    square = nodes.new('ShaderNodeMath')
    square.operation = 'MULTIPLY'
    links.new(gray.outputs['Val'], square.inputs[0])
    links.new(gray.outputs['Val'], square.inputs[1])
    gain = nodes.new('ShaderNodeMath')
    gain.operation = 'MULTIPLY'
    gain.inputs[1].default_value = 3.2
    links.new(square.outputs[0], gain.inputs[0])
    add = nodes.new('ShaderNodeMath')
    add.operation = 'ADD'
    links.new(gray.outputs['Val'], add.inputs[0])
    links.new(gain.outputs[0], add.inputs[1])
    clamp = nodes.new('ShaderNodeMath')
    clamp.operation = 'MINIMUM'
    clamp.inputs[1].default_value = .90
    links.new(add.outputs[0], clamp.inputs[0])
    emission = nodes.new('ShaderNodeEmission')
    links.new(clamp.outputs[0], emission.inputs['Color'])
    output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    for link in list(output.inputs['Surface'].links):
        links.remove(link)
    links.new(emission.outputs[0], output.inputs['Surface'])
    image = bpy.data.images.new('Demon_White_Claw_Colour', width=2048, height=2048)
    image.colorspace_settings.name = 'sRGB'
    target = nodes.new('ShaderNodeTexImage')
    target.image = image
    nodes.active = target
    data.materials.append(material)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.bake(type='EMIT', margin=16, use_selected_to_active=False, use_clear=True)
    image.filepath_raw = str(stage / 'textures/white_claw_base_color.png')
    image.file_format = 'PNG'
    image.save()
    image.pack()
    claws = mesh.data.materials[3]
    shader = next(n for n in claws.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for link in list(shader.inputs['Base Color'].links):
        claws.node_tree.links.remove(link)
    texture = claws.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image = image
    claws.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])
    shader.inputs['Base Color'].default_value = (1, 1, 1, 1)
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(data)
    bpy.data.materials.remove(material)
    bpy.data.scenes.remove(scratch)
    bpy.context.window.scene = scene
    print('Baked white talon pigment with preserved dark roots and surface variation.')
