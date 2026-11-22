"""Zoomed x-ray clay views with 5 cm grids for reading joints. Usage: zoom_views.py <blend> <prefix> <cx> <cy> <cz> <size>"""
import bpy, os, sys
from mathutils import Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
cx, cy, cz, s = map(float, a[2:6])
C.floor_grid(); fl = bpy.data.objects['Floor']
for name, rot, loc in (('WallXZ', Matrix.Rotation(1.5708, 4, 'X'), (0, 1.2, 0)),
                       ('WallYZ', Matrix.Rotation(1.5708, 4, 'Y'), (-1.2, 0, 0))):
    o = fl.copy(); o.name = name; bpy.context.scene.collection.objects.link(o)
    o.matrix_world = Matrix.Translation(loc) @ rot
rig = bpy.data.objects.get(C.RIG)
for view, (loc, extra) in {'front': ((cx, cy - 4, cz), ('WallXZ',)), 'side': ((cx + 4, cy, cz), ('WallYZ',)),
                           'top': ((cx, cy, cz + 4), ())}.items():
    C.render(loc, (cx, cy, cz), s, os.path.join(HERE, 'review', f'{a[1]}_{view}.png'), res=(900, 900),
             bones=rig is not None, extra=extra)
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = False
