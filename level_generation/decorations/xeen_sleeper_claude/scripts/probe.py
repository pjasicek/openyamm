"""Survey (Blender): rest-pose bone frames of the titan and workbench renders of chosen clip frames.
Usage: blender -b --python probe.py -- <out_dir> action:frame [action:frame ...]"""
import math, os, sys
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import posing
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[0]; os.makedirs(out, exist_ok=True)
arm, body = posing.import_creature(os.path.join(REPO, 'assets_source/worlds/mm6/models/mm6_ttn.glb'))
print('ARM matrix', arm.matrix_world)
for b in arm.data.bones:
    m = arm.matrix_world @ b.matrix_local
    print('BONE %-22s head %s x %s y %s z %s' % (b.name, tuple(round(v, 3) for v in m.translation),
          tuple(round(v, 2) for v in m.col[0][:3]), tuple(round(v, 2) for v in m.col[1][:3]),
          tuple(round(v, 2) for v in m.col[2][:3])))
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 400, 400
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.2
for spec in argv[1:]:
    act, fr = spec.split(':')
    posing.apply_pose(arm, {'base': [act, float(fr)]})
    for view, d in (('front', Vector((0, -6, 0))), ('side', Vector((6, 0, 0))), ('top', Vector((0, -0.01, 6)))):
        c = Vector((0, 0, 0.8))
        cam.location = c + d
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(out, f'{act}_{fr}_{view}.png')
        bpy.ops.render.render(write_still=True)
print('PROBE_DONE')
