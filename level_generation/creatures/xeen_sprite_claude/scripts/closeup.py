"""Workbench clay close-ups of Body around a point. Args: -- <blend> <out prefix> <x> <y> <z> <size> [views...]
views: front back left right top bottom three_quarter (default front left)."""
import bpy, sys, os, math
import os as _os; _os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # project-relative paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, out = a[0], a[1]; x, y, z, size = map(float, a[2:6]); views = a[6:] or ['front', 'left']
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.show_wire = True
scene = bpy.context.scene; common.workbench_clay(scene)
DIRS = {'front': (0, -1, 0), 'back': (0, 1, 0), 'left': (1, 0, 0), 'right': (-1, 0, 0), 'top': (0, 0, 1),
        'bottom': (0, 0, -1), 'three_quarter': (0.57, -0.82, 0.0)}
from mathutils import Vector
scene.render.resolution_x = scene.render.resolution_y = 700
for v in views:
    d = Vector(DIRS[v]).normalized()
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = size
    cam = bpy.data.objects.new('c', cd); scene.collection.objects.link(cam)
    cam.location = Vector((x, y, z)) + d * 5
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y' if abs(d.z) < 0.9 else 'X').to_euler()
    scene.camera = cam; scene.render.filepath = f'{os.path.abspath(out)}_{v}.png'
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
print('CLOSEUP', out, views)
