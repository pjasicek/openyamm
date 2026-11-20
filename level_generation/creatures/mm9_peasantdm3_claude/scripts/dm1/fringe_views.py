"""Close-ups of the fringe / hairline (orchestrator lesson 2026-11-01) of a GLB at bind pose: the camera aims at the forehead
(the highest head vertex height minus 0.07 m, front-most face point). Args: -- <glb> <out png>"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and 'LOD' not in o.name and 'Shadow' not in o.name]
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in meshes:
        o.hide_render = True
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for o in meshes:
    me = o.evaluated_get(dg).to_mesh(); pts += [o.matrix_world @ v.co for v in me.vertices]; o.evaluated_get(dg).to_mesh_clear()
top = max(p.z for p in pts)
fz = top - 0.075
band = [p for p in pts if abs(p.z - fz) < 0.02 and abs(p.x) < 0.05]
front = min(band, key=lambda p: p.y)     # the model faces -Y in Blender
c = Vector((0.0, front.y + 0.04, fz))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 520
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.6, 0.6, 0.62)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.17
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
import os
outs = []
for name, d in (('front', (0, -1, 0)), ('above', (0, -1, 0.7)), ('q34r', (-0.8, -1, 0.35)), ('q34l', (0.8, -1, 0.35))):
    d = Vector(d).normalized(); cam.location = c + d * 2
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    fn = f'/tmp/fringe_{os.getpid()}_{name}.png'; sc.render.filepath = fn; bpy.ops.render.render(write_still=True); outs.append(fn)
imgs = [bpy.data.images.load(f) for f in outs]
W = 520
out = bpy.data.images.new('sheet', W * len(imgs), W)
import numpy as np
buf = np.zeros((W, W * len(imgs), 4), np.float32)
for i, im in enumerate(imgs):
    px = np.array(im.pixels[:], np.float32).reshape(W, W, 4); buf[:, i * W:(i + 1) * W] = px
out.pixels = buf.ravel(); out.filepath_raw = a[1]; out.file_format = 'PNG'; out.save()
print('FRINGE_VIEWS', a[1])
