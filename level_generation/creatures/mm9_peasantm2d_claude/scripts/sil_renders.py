"""Silhouette masks (transparent film) of a GLB at bind pose from fixed ortho cameras. Args: glb out_prefix size ortho cx,cy,cz"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, pre, size, ortho = a[0], a[1], int(a[2]), float(a[3])
c = Vector([float(x) for x in a[4].split(',')])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'ARMATURE':
        if o.animation_data: o.animation_data.action = None
        for pb in o.pose.bones: pb.matrix_basis.identity()
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (1, 1, 1)
sc.display.shading.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
sc.render.film_transparent = True
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
for v, d in {'front': Vector((0, -1, 0)), 'right': Vector((-1, 0, 0)), 'q34': Vector((-1, -1.25, 0.3))}.items():
    d = d.normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{pre}_{v}.png'; bpy.ops.render.render(write_still=True)
print('SIL done')
