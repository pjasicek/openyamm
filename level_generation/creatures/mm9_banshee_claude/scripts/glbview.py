"""Workbench views of a GLB's meshes. Args: glb out_prefix ortho cx,cy,cz [views comma]"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, pre, ortho = a[0], a[1], float(a[2])
c = Vector([float(x) for x in a[3].split(',')])
views = a[4].split(',') if len(a) > 4 else ['front', 'left', 'back', 'q34', 'below', 'top']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.75, .72, .68); sh.show_backface_culling = False; sh.show_cavity = True; sh.cavity_type = 'WORLD'
sc.render.resolution_x = 900; sc.render.resolution_y = 900
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
D = {'front': (0, -1, .02), 'left': (1, 0, .02), 'right': (-1, 0, .02), 'back': (0, 1, .02), 'q34': (-1, -1.25, .35), 'below': (0, -.25, -1), 'top': (0, -.25, 1), 'hand': (-.6, -.3, .75)}
for n in views:
    d = Vector(D[n]).normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{pre}_{n}.png'; bpy.ops.render.render(write_still=True)
