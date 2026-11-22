"""X-ray clay views of work/<blend> over a 5 cm floor grid (10 cm lines thicker) plus vertical grid planes, for
reading joint positions. Usage: grid_views.py <blend> <prefix>"""
import bpy, os, sys, bmesh
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', argv[0]))
# vertical grids: a copy of the floor grid rotated into the XZ (back wall) and YZ (side wall) planes
C.floor_grid()
fl = bpy.data.objects['Floor']
for name, rot, loc in (('WallXZ', Matrix.Rotation(1.5708, 4, 'X'), (0, 1.2, 0)), ('WallYZ', Matrix.Rotation(1.5708, 4, 'Y'), (-1.2, 0, 0))):
    o = fl.copy(); o.name = name; bpy.context.scene.collection.objects.link(o)
    o.matrix_world = Matrix.Translation(loc) @ rot
rig = bpy.data.objects.get(C.RIG)
for view, (loc, tgt, extra) in {'front': ((0, -4, 0.4), (0, 0, 0.4), ('WallXZ',)),
                                'side': ((4, 0, 0.4), (0, 0, 0.4), ('WallYZ',)),
                                'top': ((0, 0, 4), (0, 0, 0), ())}.items():
    C.render(loc, tgt, 2.3, os.path.join(HERE, 'review', f'{argv[1]}_{view}.png'), res=(1000, 1000),
             bones=rig is not None, extra=extra)
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = False
