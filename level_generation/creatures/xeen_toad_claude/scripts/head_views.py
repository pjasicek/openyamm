"""Close clay views of the head over 5 cm grid walls (side from +x, front, three-quarter): review/head_*.png"""
import bpy, os, sys
from mathutils import Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', argv[0] if argv else 'clean_v1.blend'))
C.floor_grid()
fl = bpy.data.objects['Floor']
for name, rot, loc in (('WallXZ', Matrix.Rotation(1.5708, 4, 'X'), (0, 1.2, 0)), ('WallYZ', Matrix.Rotation(1.5708, 4, 'Y'), (-1.2, 0, 0))):
    o = fl.copy(); o.name = name; bpy.context.scene.collection.objects.link(o)
    o.matrix_world = Matrix.Translation(loc) @ rot
for view, (loc, tgt, extra) in {'side': ((4, -0.65, 0.55), (0, -0.65, 0.55), ('WallYZ',)),
                                'front': ((0, -4, 0.55), (0, -0.65, 0.55), ('WallXZ',)),
                                'quarter': ((2.5, -3.2, 1.2), (0, -0.65, 0.5), ())}.items():
    C.render(loc, tgt, 0.8, os.path.join(HERE, 'review', f'head_{view}.png'), res=(800, 800), extra=extra)
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = False
