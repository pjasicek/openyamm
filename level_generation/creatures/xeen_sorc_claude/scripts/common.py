"""Shared helpers for the bar1 Blender pipeline (run inside background Blender)."""
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
    angles = {'front': 0.0, 'left': 90.0, 'back': 180.0, 'right': -90.0, 'three_quarter': 35.0, 'side60': 60.0, 'rside60': -60.0}
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
import bpy, bmesh
from mathutils import Vector, Matrix

MESH, RIG = 'Witch', 'Witch_Rig'


def look(loc, target):
    fwd = (Vector(target) - Vector(loc)).normalized()
    upw = Vector((0, 1, 0)) if abs(fwd.z) > 0.95 else Vector((0, 0, 1))
    right = fwd.cross(upw).normalized(); up = right.cross(fwd)
    return Matrix.Translation(Vector(loc)) @ Matrix((right, up, -fwd)).transposed().to_4x4()


def setup(textured=False, bones=False):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'FLAT' if textured else 'STUDIO'; sh.show_cavity = not textured; sh.show_shadows = False
    sh.color_type = 'TEXTURE' if textured else 'SINGLE'; sh.single_color = (0.78, 0.74, 0.66)
    sh.background_type = 'VIEWPORT'; sh.background_color = (0.82, 0.82, 0.8)
    sh.show_xray = bones; sh.xray_alpha = 0.6


def floor_grid():
    """A 1.6 m floor plate with 5 cm lines (an object called Floor)."""
    if bpy.data.objects.get('Floor'):
        return
    bm = bmesh.new()
    for i in range(-24, 25):
        for a, b in (((i * 0.05, -1.2, 0), (i * 0.05, 1.2, 0)), ((-1.2, i * 0.05, 0), (1.2, i * 0.05, 0))):
            m = Matrix.Translation((Vector(a) + Vector(b)) / 2)
            d = Vector(b) - Vector(a)
            m = m @ d.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.002 if i % 2 else 0.005,
                                  radius2=0.002 if i % 2 else 0.005, depth=d.length, matrix=m)
    me = bpy.data.meshes.new('Floor'); bm.to_mesh(me)
    o = bpy.data.objects.new('Floor', me); bpy.context.scene.collection.objects.link(o)
    mat = bpy.data.materials.new('floor'); mat.diffuse_color = (0.35, 0.35, 0.4, 1); me.materials.append(mat)


def render(loc, target, scale, path, res=(560, 400), bones=False, textured=False, floor=True, extra=()):
    sc = bpy.context.scene
    setup(textured, bones)
    sc.render.resolution_x, sc.render.resolution_y = res
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = scale
    cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam)
    cam.matrix_world = look(loc, target)
    sc.camera = cam
    rods = None
    rig = bpy.data.objects.get(RIG)
    if bones and rig:
        bm = bmesh.new()
        for b in rig.pose.bones:
            h = rig.matrix_world @ b.head; t = rig.matrix_world @ b.tail; v = t - h
            if v.length < 1e-5:
                continue
            m = Matrix.Translation((h + t) / 2) @ v.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.006, radius2=0.002, depth=v.length, matrix=m)
        me = bpy.data.meshes.new('rods'); bm.to_mesh(me); rods = bpy.data.objects.new('rods', me)
        sc.collection.objects.link(rods)
        mat = bpy.data.materials.new('r'); mat.diffuse_color = (1, 0.1, 0.1, 1); me.materials.append(mat)
        sc.display.shading.color_type = 'MATERIAL'
    if floor:
        floor_grid()
    keep = {MESH, 'Tongue', 'rods', 'Floor' if floor else '', *extra}
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = o.name not in keep
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    if rods:
        bpy.data.objects.remove(rods, do_unlink=True)


VIEWS = {'side': ((-2.5, 0.0, 0.22), (0, 0, 0.22)), 'front': ((0, -2.5, 0.22), (0, 0, 0.22)),
         'top': ((0, 0.0, 2.5), (0, 0, 0)), 'quarter': ((-1.7, -1.8, 1.1), (0, 0, 0.18)),
         'back': ((0, 2.5, 0.22), (0, 0, 0.22)), 'under': ((0, 0, -2.5), (0, 0, 0.2))}
