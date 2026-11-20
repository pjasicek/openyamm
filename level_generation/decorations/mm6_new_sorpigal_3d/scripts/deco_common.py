"""Shared Blender helpers for the New Sorpigal 3D decoration props: scene reset, lighting, camera framing, renders."""
import bpy, math, os
from mathutils import Vector

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..'))
NATIVE = os.path.join(REPO, 'level_generation', 'decorations', 'mm6_new_sorpigal')


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_gltf(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def world_bounds(objects):
    pts = [o.matrix_world @ Vector(c) for o in objects if o.type == 'MESH' for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def setup_render(resolution=(512, 512), engine='EEVEE'):
    scene = bpy.context.scene
    if engine == 'EEVEE':
        for name in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
            try:
                scene.render.engine = name
                break
            except TypeError:
                continue
    else:
        scene.render.engine = engine
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    world = scene.world or bpy.data.worlds.new('World')
    scene.world = world
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1.0)
    bg.inputs['Strength'].default_value = 0.9
    sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 3.2; sun.angle = math.radians(3)
    so = bpy.data.objects.new('Sun', sun); scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(40), 0, math.radians(-35))
    return scene


def frame_camera(objects, yaw_deg=0.0, elevation_deg=15.0, margin=1.08, lens=50):
    """Perspective camera looking at the objects' bounds from `yaw_deg` (0 = from -Y) at `elevation_deg`."""
    scene = bpy.context.scene
    lo, hi = world_bounds(objects)
    centre = (lo + hi) / 2
    radius = (hi - lo).length / 2
    cam = scene.camera
    if cam is None:
        cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
        scene.collection.objects.link(cam); scene.camera = cam
    cam.data.lens = lens
    fov = 2 * math.atan(cam.data.sensor_width / (2 * lens))
    dist = radius * margin / math.sin(fov / 2)
    yaw, el = math.radians(yaw_deg), math.radians(elevation_deg)
    d = Vector((math.sin(yaw) * math.cos(el), -math.cos(yaw) * math.cos(el), math.sin(el)))
    cam.location = centre + d * dist
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    return cam


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
