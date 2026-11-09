"""Shared render helpers for the rat (run inside Blender)."""
import bpy
from mathutils import Vector, Matrix


def render_ortho(loc, target, scale, path, bones=False, res=(560, 420), textured=False):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.show_cavity = not textured; sh.show_shadows = False
    sh.color_type = 'TEXTURE' if textured else 'SINGLE'; sh.single_color = (0.78, 0.72, 0.64)
    sh.background_type = 'VIEWPORT'; sh.background_color = (0.82, 0.82, 0.8)
    sh.show_xray = bones; sh.xray_alpha = 0.7
    sc.render.resolution_x, sc.render.resolution_y = res
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = scale
    cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam)
    d = (Vector(target) - Vector(loc)).normalized()
    cam.matrix_world = Matrix.Translation(Vector(loc)) @ d.to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    sc.camera = cam
    rig = bpy.data.objects.get('Bat_Rig')
    rods = None
    if bones and rig:
        import bmesh
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
        sh.color_type = 'MATERIAL'
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = o.name not in ('Bat', 'rods')
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    if rods:
        bpy.data.objects.remove(rods, do_unlink=True)
