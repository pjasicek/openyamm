"""Render BModel OBJs of the map's source (source/models) one by one with their textures, from the front
three-quarter (the front is read from the house's event face), for reviewing the house kit (houses.py).

    blender --background --factory-startup --python level_generation/projects/hesper_out1/render_bmodels.py -- \
        <out folder> <model name> [...]
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parent
ART = PROJECT.parents[2] / 'design/kreegan_world/art'
args = sys.argv[sys.argv.index('--') + 1:]
out = Path(args[0])
out.mkdir(parents=True, exist_ok=True)
textures = {}
for folder in ['textures_d0/blv', 'textures_out1/masters', 'textures_interiors/masters']:
    for png in (ART / folder).glob('*.png'):
        textures[png.stem] = png


def material(name):
    existing = bpy.data.materials.get('r_' + name)
    if existing:
        return existing
    mat = bpy.data.materials.new('r_' + name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.8
    node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = bpy.data.images.load(str(textures[name]), check_existing=True)
    mat.node_tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
    return mat


for name in args[1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=str(PROJECT / 'source/models' / f'{name}.obj'), forward_axis='Y', up_axis='Z')
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for obj in objects:
        for slot in obj.material_slots:
            key = slot.material.name.split('.')[0]
            if key in textures:
                slot.material = material(key)
        obj.data.materials  # noqa
    mesh_points = [o.matrix_world @ v.co for o in objects for v in o.data.vertices]
    low = Vector([min(p[i] for p in mesh_points) for i in range(3)])
    high = Vector([max(p[i] for p in mesh_points) for i in range(3)])
    centre, size = (low + high) / 2, (high - low).length
    # The front: the door face is the one material named like a door or cage.
    front = Vector((0, -1, 0))
    for obj in objects:
        for poly in obj.data.polygons:
            key = obj.material_slots[poly.material_index].material.name
            if any(tag in key for tag in ('door', 'cage', 'stall')):
                front = (obj.matrix_world.to_3x3() @ poly.normal).normalized()
                front.z = 0
                front.normalize()
                break
    side = Vector((-front.y, front.x, 0))
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    camera.location = centre + (front * 0.85 + side * 0.55) * size + Vector((0, 0, size * 0.35))
    camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.lens = 35
    bpy.context.scene.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    bpy.context.scene.collection.objects.link(sun)
    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.52, 0.58, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8
    bpy.context.scene.world = world
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in
                                                                           bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = 960, 640
    scene.render.filepath = str(out / f'{name}.png')
    bpy.ops.render.render(write_still=True)
    print('RENDERED', name)
