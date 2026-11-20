"""Shared Blender setup for the clump-card renders: the Poly Haven grass import, flat soft lighting and an
orthographic camera. Imported by render_cards.py and preview_clump.py (run inside Blender)."""
import math
import os

import bpy
from mathutils import Vector


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def eevee(scene, resolution):
    for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '16'
    scene.render.filter_size = 1.0
    scene.eevee.taa_render_samples = 64
    scene.eevee.use_shadows = False
    for attr in ('use_fast_gi', 'use_raytracing', 'use_gtao'):
        if hasattr(scene.eevee, attr):
            setattr(scene.eevee, attr, False)


def flat_light(scene, ambient=1.0, top=0.9):
    """Mostly ambient (a uniform white world) plus a gentle, shadowless top light."""
    world = scene.world or bpy.data.worlds.new('World')
    scene.world = world
    world.use_nodes = True
    background = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    background.inputs['Color'].default_value = (1, 1, 1, 1)
    background.inputs['Strength'].default_value = ambient
    sun = bpy.data.objects.new('Top', bpy.data.lights.new('Top', 'SUN'))
    scene.collection.objects.link(sun)
    sun.data.energy = top
    sun.data.use_shadow = False
    sun.rotation_euler = (math.radians(15), 0, math.radians(20))


def ortho_camera(scene, name='Camera'):
    camera = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    camera.data.type = 'ORTHO'
    camera.data.clip_start = 0.001
    camera.data.clip_end = 100
    scene.collection.objects.link(camera)
    scene.camera = camera
    return camera


def aim(camera, target, yaw_degrees, pitch_degrees, distance=10.0):
    """Camera looking at target from yaw (0 = from -Y towards +Y) and pitch degrees below the horizon."""
    yaw, pitch = math.radians(yaw_degrees), math.radians(pitch_degrees)
    direction = Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
    camera.location = Vector(target) + direction * distance
    camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()


def import_grass(gltf, alpha_png):
    """Imports the Poly Haven glTF (every variant at its own x offset) and wires the alpha map, which the glTF
    leaves out, into an alpha-clipped material. Returns the imported mesh objects by node name."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=gltf)
    objects = {o.name: o for o in bpy.data.objects if o not in before and o.type == 'MESH'}
    alpha = bpy.data.images.load(alpha_png)
    alpha.colorspace_settings.name = 'Non-Color'
    for material in {slot.material for o in objects.values() for slot in o.material_slots if slot.material}:
        tree = material.node_tree
        bsdf = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
        texture = next(n for n in tree.nodes if n.type == 'TEX_IMAGE' and n.image and 'diff' in n.image.name)
        alpha_node = tree.nodes.new('ShaderNodeTexImage')
        alpha_node.image = alpha
        if texture.inputs['Vector'].links:
            tree.links.new(texture.inputs['Vector'].links[0].from_socket, alpha_node.inputs['Vector'])
        # Hard alpha clip at 0.5, as the game's alpha test does.
        clip = tree.nodes.new('ShaderNodeMath')
        clip.operation = 'GREATER_THAN'
        clip.inputs[1].default_value = 0.5
        tree.links.new(alpha_node.outputs['Color'], clip.inputs[0])
        tree.links.new(clip.outputs[0], bsdf.inputs['Alpha'])
        # Matte foliage: no specular highlights, no normal-map relief from the photoscan.
        bsdf.inputs['Specular IOR Level'].default_value = 0.0
        bsdf.inputs['Roughness'].default_value = 1.0
        for link in list(bsdf.inputs['Normal'].links):
            tree.links.remove(link)
        for link in list(bsdf.inputs['Roughness'].links):
            tree.links.remove(link)
        for link in list(bsdf.inputs['Metallic'].links):
            tree.links.remove(link)
        bsdf.inputs['Metallic'].default_value = 0.0
        material.surface_render_method = 'DITHERED'
        material.use_backface_culling = False
    return objects


def save(scene, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
