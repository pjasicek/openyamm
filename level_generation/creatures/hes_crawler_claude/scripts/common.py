"""Shared render helpers for the crawler (run inside Blender)."""
import bpy, bmesh
from mathutils import Vector, Matrix

MESH, RIG = 'Crawler', 'Crawler_Rig'


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
    for i in range(-16, 17):
        for a, b in (((i * 0.05, -0.8, 0), (i * 0.05, 0.8, 0)), ((-0.8, i * 0.05, 0), (0.8, i * 0.05, 0))):
            m = Matrix.Translation((Vector(a) + Vector(b)) / 2)
            d = Vector(b) - Vector(a)
            m = m @ d.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.0015 if i % 2 else 0.003,
                                  radius2=0.0015 if i % 2 else 0.003, depth=d.length, matrix=m)
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
    keep = {MESH, 'rods', 'Floor' if floor else '', *extra}
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
