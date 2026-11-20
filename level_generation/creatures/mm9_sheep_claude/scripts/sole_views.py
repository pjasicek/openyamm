"""Ortho close-ups of the hooves from below and front (diagnosis). Args: <blend> <outdir> <prefix>"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
src, out, pre = argv[:3]
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
keep = ('Body', 'Sheep', 'Ram', 'body.mesh')
for o in sc.objects:
    if o.type == 'MESH' and o.name not in keep:
        o.hide_render = True
for arm in [o for o in sc.objects if o.type == 'ARMATURE']:
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
bpy.context.view_layer.update()
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for name, c, s in (('front_pair', Vector((0, -0.27, 0.05)), 0.46), ('hind_pair', Vector((0, 0.5, 0.05)), 0.46)):
    cd.ortho_scale = s
    for v, d in (('below', Vector((0, 0.0001, -1))), ('front', Vector((0, -1, 0.05)))):
        cam.location = c + d.normalized() * 3
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{pre}_{name}_{v}.png'); bpy.ops.render.render(write_still=True)
