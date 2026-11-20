"""Shared helpers for the ooze Blender pipeline (run inside background Blender)."""
import bpy
import addon_utils
import math
import os
from mathutils import Vector

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(PROJECT, 'work')
REVIEW = os.path.join(PROJECT, 'review')


def enable_mpfb():
    addon_utils.enable('bl_ext.blender_org.mpfb', default_set=True)


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def world_bounds(objects):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        for v in mesh.vertices:
            p = obj.matrix_world @ v.co
            lo = Vector(map(min, lo, p))
            hi = Vector(map(max, hi, p))
        evaluated.to_mesh_clear()
    return lo, hi


def setup_render(resolution=(768, 1152), engine='BLENDER_EEVEE_NEXT'):
    scene = bpy.context.scene
    for candidate in (engine, 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'):
        try:
            scene.render.engine = candidate
            break
        except TypeError:
            continue
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new('World')
    scene.world.color = (0.82, 0.82, 0.8)
    return scene


def ortho_camera(name, location, rotation, scale):
    data = bpy.data.cameras.new(name)
    data.type = 'ORTHO'
    data.ortho_scale = scale
    cam = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = location
    cam.rotation_euler = rotation
    return cam


def workbench_clay(scene, textured=False):
    scene.render.engine = 'BLENDER_WORKBENCH'
    shading = scene.display.shading
    shading.light = 'STUDIO'
    shading.color_type = 'TEXTURE' if textured else 'MATERIAL'
    shading.show_cavity = not textured
    shading.show_shadows = False
    shading.background_type = 'VIEWPORT'
    shading.background_color = (0.82, 0.82, 0.8)


def render_views(path_prefix, center_z, height, views=('front', 'left', 'back', 'right'), distance=6.0,
                 resolution=(512, 768), target=(0.0, 0.0)):
    """Orthographic turnaround. Character faces -Y (Blender), so 'front' camera sits at -Y."""
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = resolution
    angles = {'front': 0.0, 'left': 90.0, 'back': 180.0, 'right': -90.0, 'three_quarter': 35.0}
    outputs = []
    for view in views:
        a = math.radians(angles[view])
        # Rotate camera around Z; 'left' shows the character's left side (camera at -X... character left is +X).
        x = target[0] + math.sin(a) * distance
        y = target[1] - math.cos(a) * distance
        cam = ortho_camera('cam_' + view, (x, y, center_z), (math.radians(90), 0, a), height)
        scene.camera = cam
        scene.render.filepath = f'{path_prefix}_{view}.png'
        bpy.ops.render.render(write_still=True)
        outputs.append(scene.render.filepath)
        bpy.data.objects.remove(cam, do_unlink=True)
    return outputs
