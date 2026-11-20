"""Shared Blender helpers for the Hound (run inside Blender). Forward is -Y, up +Z, creature left +X."""
import os
import bpy
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESH = 'Hound'
RIG = 'Hound_Rig'


def path(*parts):
    return os.path.join(HERE, *parts)


def render_ortho(loc, target, scale, out, show=None, res=(900, 600), textured=False, bones=False, color=None,
                 xray=False, bg=(0.82, 0.82, 0.8)):
    """Workbench orthographic render. show: object names to render (default: every mesh)."""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.show_cavity = not textured
    sh.show_shadows = False
    sh.color_type = 'TEXTURE' if textured else ('MATERIAL' if color == 'material' else 'SINGLE')
    sh.single_color = (0.78, 0.72, 0.64)
    sh.background_type = 'VIEWPORT'
    sh.background_color = bg
    sh.show_xray = xray or bones
    sh.xray_alpha = 0.7
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    cd = bpy.data.cameras.new('c')
    cd.type = 'ORTHO'
    cd.ortho_scale = scale
    cd.clip_start = 0.01
    cd.clip_end = 100
    cam = bpy.data.objects.new('c', cd)
    sc.collection.objects.link(cam)
    d = (Vector(target) - Vector(loc)).normalized()
    cam.matrix_world = Matrix.Translation(Vector(loc)) @ d.to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    sc.camera = cam
    rods = None
    rig = bpy.data.objects.get(RIG)
    if bones and rig:
        import bmesh
        bm = bmesh.new()
        for b in rig.pose.bones:
            h = rig.matrix_world @ b.head
            t = rig.matrix_world @ b.tail
            v = t - h
            if v.length < 1e-5:
                continue
            m = Matrix.Translation((h + t) / 2) @ v.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.012, radius2=0.004, depth=v.length,
                                  matrix=m)
        me = bpy.data.meshes.new('rods')
        bm.to_mesh(me)
        rods = bpy.data.objects.new('rods', me)
        sc.collection.objects.link(rods)
        mat = bpy.data.materials.new('r')
        mat.diffuse_color = (1, 0.1, 0.1, 1)
        me.materials.append(mat)
        sh.color_type = 'MATERIAL'
    names = set(show) if show else None
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = not (o.name == 'rods' or names is None or o.name in names)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    if rods:
        bpy.data.objects.remove(rods, do_unlink=True)
