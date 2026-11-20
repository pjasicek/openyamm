"""Filmstrip of a GLB clip for review by eye: orthographic side, front and three-quarter views at evenly spaced
phases, each view a row, the floor drawn as a thin plane at 0 and a grid of 0.25 model units behind the body, so
planted paws, the swing, knees and elbows, the tail and the floor can be read. Workbench (solid, texture colours).

    blender -b --factory-startup -P filmstrip.py -- <glb> <clip> <out.png> [frames 8] [views side,front,quarter]
"""
import bpy, sys, os, math
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
GLB, CLIP, OUT = args[0], args[1], os.path.abspath(args[2])
N = int(args[3]) if len(args) > 3 else 8
VIEWS = args[4].split(',') if len(args) > 4 else ['side', 'front', 'quarter']
SIZE = 360

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(GLB))
scene = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes:                                     # LOD0 only
    if any(k in o.name for k in ('LOD1', 'LOD2', 'LOD3', 'Shadow')):
        o.hide_render = True
act = bpy.data.actions[CLIP] if CLIP in bpy.data.actions else next(a for a in bpy.data.actions if a.name.startswith(CLIP))
rig.animation_data.action = act
if len(getattr(act, 'slots', [])):
    rig.animation_data.action_slot = act.slots[0]
start, end = act.frame_range
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, -0.002))
floor = bpy.context.object
mat = bpy.data.materials.new('floor'); mat.diffuse_color = (0.35, 0.42, 0.35, 1); floor.data.materials.append(mat)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_cavity = True
scene.render.resolution_x = SIZE; scene.render.resolution_y = SIZE
scene.render.film_transparent = False
cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = 4.4
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam); scene.camera = cam
# the model faces -Y in Blender after import (glTF +Z forward)
POS = {'side': Vector((6, -0.0, 1.1)), 'rside': Vector((-6, 0.0, 1.1)), 'front': Vector((0, -6, 1.1)), 'quarter': Vector((4.2, -4.2, 2.2)),
       'back': Vector((0, 6, 1.1)), 'below': Vector((3, -0.1, 0.25))}
target = Vector((0, -0.0, 1.0))
tmp = os.path.splitext(OUT)[0] + '_frames'
os.makedirs(tmp, exist_ok=True)
paths = []
for view in VIEWS:
    cam.location = POS[view]
    cam.rotation_euler = (cam.location - target).to_track_quat('Z', 'Y').to_euler()
    row = []
    for k in range(N):
        f = start + (end - start) * k / N
        scene.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        p = os.path.join(tmp, f'{view}_{k:02d}.png')
        scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        row.append(p)
    paths.append(row)
import numpy as np
rows = []
for row in paths:
    imgs = []
    for p in row:
        im = bpy.data.images.load(p)
        a = np.array(im.pixels[:]).reshape(SIZE, SIZE, 4)[::-1]
        imgs.append(a)
        bpy.data.images.remove(im)
    rows.append(np.concatenate(imgs, axis=1))
sheet = np.concatenate(rows, axis=0)
h, w = sheet.shape[:2]
img = bpy.data.images.new('sheet', w, h, alpha=True)
img.pixels = sheet[::-1].ravel()
img.filepath_raw = OUT; img.file_format = 'PNG'; img.save()
print('SHEET', OUT, N, 'phases', VIEWS)
