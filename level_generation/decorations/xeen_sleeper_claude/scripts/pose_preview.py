"""Workbench previews of the posed titan: standing front/side and laid down (top, side, three-quarter).
Usage: blender -b --python pose_preview.py -- <out_prefix>"""
import json, math, os, sys
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pose_sleeper, posing
cfg = json.load(open(os.path.join(HERE, 'sleeper.json')))
out = sys.argv[sys.argv.index('--') + 1]
arm, body = pose_sleeper.pose(cfg)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 500, 500
def make_cam():
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    scene.collection.objects.link(cam); scene.camera = cam
    cam.data.type = 'ORTHO'
    return cam

cam = make_cam()

def shot(name, c, d, scale):
    cam.data.ortho_scale = scale
    cam.location = Vector(c) + Vector(d)
    cam.rotation_euler = (-Vector(d)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{out}_{name}.png'
    bpy.ops.render.render(write_still=True)

shot('stand_front', (0, 0, 0.9), (0, -6, 0), 1.0)
shot('stand_side', (0, 0, 0.9), (6, 0, 0), 1.0)
static = posing.bake_static(arm, body)
static.data.transform(pose_sleeper.LAY)
cam = make_cam()
lo = [min(v.co[i] for v in static.data.vertices) for i in range(3)]
hi = [max(v.co[i] for v in static.data.vertices) for i in range(3)]
print('LAID bounds', [round(x, 3) for x in lo], [round(x, 3) for x in hi])
c = [(a + b) / 2 for a, b in zip(lo, hi)]
shot('lay_top', c, (0, -0.01, 6), 1.8)
shot('lay_front', c, (0, -6, 0), 1.8)
shot('lay_q', c, (2.5, -4, 2.5), 1.8)
shot('lay_head', (lo[0] + 0.2, c[1], c[2]), (-1.5, -4, 2.5), 0.8)
print('PREVIEW_DONE')
