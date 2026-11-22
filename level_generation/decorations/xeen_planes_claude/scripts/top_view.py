"""Top-down orthographic render of GLBs (model front, Blender -Y, at the bottom of the image).
Usage: blender -b --python top_view.py -- <out.png> <glb> [<glb> ...]"""
import sys
import bpy
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
out, glbs = argv[0], argv[1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
x = 0.0
for g in glbs:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=g)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if '_LOD' in o.name:
            o.hide_render = True
    pts = [o.matrix_world @ v.co for o in new if o.type == 'MESH' and not o.hide_render for v in o.data.vertices]
    w = max(p.x for p in pts) - min(p.x for p in pts)
    for o in new:
        o.location.x += x + w / 2
    x += w * 1.1
s.render.engine = 'BLENDER_WORKBENCH'
s.display.shading.light = 'FLAT'
s.display.shading.color_type = 'TEXTURE'
s.render.resolution_x, s.render.resolution_y = 1400, 500
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
cam.data.type = 'ORTHO'
cam.data.ortho_scale = x
s.collection.objects.link(cam)
s.camera = cam
cam.location = (x / 2, 0, 20)
cam.rotation_euler = (0, 0, 0)
s.render.filepath = out
bpy.ops.render.render(write_still=True)
print('TOP_DONE')
