"""Textured views of a static GLB. Args: <glb> <out png> [ortho] [cz]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = 700; sc.render.resolution_y = 1000
ms = [o for o in bpy.data.objects if o.type == 'MESH']
pts = [o.matrix_world @ v.co for o in ms for v in o.data.vertices]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)]); c = (lo + hi) / 2
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (.3, .3, .33); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = max(hi - lo) * 1.1; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
import os
for n, d in dict(front=(0, -1, 0), q=(-.6, -1, .1), side=(1, 0, 0), back=(0, 1, 0)).items():
    cam.location = c + Vector(d).normalized() * 6
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = a[1] + '_' + n + '.png'
    bpy.ops.render.render(write_still=True)
