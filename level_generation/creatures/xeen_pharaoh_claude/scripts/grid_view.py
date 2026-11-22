"""Ortho close-up with a model-space grid (glTF coords): blender -b --python grid_view.py -- <glb> <out.png> <view side|front|top|back> <cx> <cy> <cz> <size> [extra.glb ...]
Centre and size in glTF metres. Side looks from +X (glTF), front from +Z, top from +Y, back from -Z."""
import sys, math, bpy, subprocess
from mathutils import Vector, Euler
a = sys.argv[sys.argv.index('--') + 1:]
src, out, view = a[0], a[1], a[2]
cx, cy, cz, size = map(float, a[3:7])
extras = a[7:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for e in extras:
    bpy.ops.import_scene.gltf(filepath=e)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'ARMATURE':
        if o.animation_data: o.animation_data.action = None
        for pb in o.pose.bones: pb.matrix_basis.identity()
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name or o.name.startswith('Icosphere')):
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 800
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = size
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((cx, -cz, cy))  # glTF -> Blender
d = {'side': Vector((1, 0, 0)), 'front': Vector((0, -1, 0)), 'back': Vector((0, 1, 0)), 'top': Vector((0, 0, 1))}[view]
cam.location = c + d * 5
up = 'Z' if view != 'top' else 'Y'
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y' if view != 'top' else 'Z').to_euler() if view != 'top' else Euler((0, 0, 0))
if view == 'top':
    cam.rotation_euler = Euler((0, 0, 0))
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
# screen axes in glTF: side: right = -z_gltf? compute by projecting
from bpy_extras.object_utils import world_to_camera_view
def proj(p):
    v = world_to_camera_view(sc, cam, Vector(p)); return v.x, v.y
ex = proj(c + Vector((0.1, 0, 0))); ey = proj(c + Vector((0, 0.1, 0))); ez = proj(c + Vector((0, 0, 0.1)))
print('AXES', ex, ey, ez)
code = f'''
from PIL import Image, ImageDraw
import numpy as np
im = Image.open({out!r}).convert("RGB"); d = ImageDraw.Draw(im)
view = {view!r}; cx, cy, cz, s = {cx}, {cy}, {cz}, {size}
# horizontal/vertical gltf axes on screen
H = {{"side": ("z", -1), "front": ("x", 1), "back": ("x", -1), "top": ("x", 1)}}[view]
V = {{"side": ("y", 1), "front": ("y", 1), "back": ("y", 1), "top": ("z", -1)}}[view]
cen = {{"x": cx, "y": cy, "z": cz}}
for t in np.arange(-3, 3, 0.05):
    for axis, sign, horiz in ((H[0], H[1], True), (V[0], V[1], False)):
        off = (t - cen[axis]) * sign / s * 800
        p = 400 + off if horiz else 400 - off
        if 0 <= p < 800:
            col = (255, 80, 80) if abs(round(t * 10) - t * 10) < 1e-6 else (90, 90, 90)
            if horiz: d.line([(p, 0), (p, 800)], fill=col); d.text((p + 2, 2), f"{{axis}}{{t:.2f}}", fill=col)
            else: d.line([(0, p), (800, p)], fill=col); d.text((2, p + 2), f"{{axis}}{{t:.2f}}", fill=col)
im.save({out!r})
'''
subprocess.run(['/usr/bin/python3', '-c', code], check=True)
print('DONE')
