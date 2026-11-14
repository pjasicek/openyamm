"""Renders a weapon GLB (the Oblivion template or a finished skin) in the guide framing of prep.py: the four
orthographic views, textured under a flat studio light (Workbench), 1024 x 1536, transparent. The template's renders
show Codex the original design next to the plain guides.

Usage: blender --background --python render_template.py -- <template> <in.glb> <out_prefix> [guide]
Writes <out_prefix>_{front,back,left,right}.png.
"""
import bpy, sys
import numpy as np
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index('--') + 1:]
NAME, GLB, OUT = argv[0], argv[1], argv[2]
ORIENT = {'s_steelshield': [[1, 0, 0], [0, 0, -1], [0, 1, 0]]}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and (NAME != 'w_bow' or o.data.name.startswith('Bow'))]
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in meshes:
        o.hide_render = True
R = Matrix(ORIENT.get(NAME, [[1, 0, 0], [0, 1, 0], [0, 0, 1]])).to_4x4()
for o in meshes:
    o.data.transform(o.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    o.data.transform(R)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
if len(argv) > 3 and argv[3] == 'guide':
    # The plain grey guide of prep.py (same mesh, same framing).
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'SINGLE'
    scene.display.shading.single_color = (0.6, 0.6, 0.6)
else:
    scene.display.shading.light = 'FLAT'
    scene.display.shading.color_type = 'TEXTURE'
scene.render.film_transparent = True
scene.render.resolution_x, scene.render.resolution_y = 1024, 1536
scene.view_settings.view_transform = 'Standard'
co = np.concatenate([np.array([v.co for v in o.data.vertices]) for o in meshes])
ctr = Vector(((co.max(0) + co.min(0)) / 2).tolist())
ext = np.ptp(co, 0)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.ortho_scale = max(ext[2] / 0.88, max(ext[0], ext[1]) * 1.5 / 0.88)
cam.data.clip_end = 1000
scene.camera = cam
views = {'front': Vector((0, -1, 0)), 'back': Vector((0, 1, 0)), 'left': Vector((1, 0, 0)), 'right': Vector((-1, 0, 0))}
for name, d in views.items():
    cam.location = ctr + d * 200
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{OUT}_{name}.png'
    bpy.ops.render.render(write_still=True)
