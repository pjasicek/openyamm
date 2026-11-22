"""Separate the connected pieces of work/clean_v1.blend and render chosen pieces alone over grid walls (side, top,
front) to read joint positions. Usage: piece_views.py <piece index> ... ; writes review/piece<i>_<view>.png"""
import bpy, os, sys
from mathutils import Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
want = [int(a) for a in sys.argv[sys.argv.index('--') + 1:]]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
m = bpy.data.objects['Toad']
bpy.context.view_layer.objects.active = m; m.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
parts = sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: -len(o.data.vertices))
C.floor_grid()
fl = bpy.data.objects['Floor']
walls = {}
for name, rot, loc in (('WallXZ', Matrix.Rotation(1.5708, 4, 'X'), (0, 1.2, 0)), ('WallYZ', Matrix.Rotation(1.5708, 4, 'Y'), (-1.2, 0, 0))):
    o = fl.copy(); o.name = name; bpy.context.scene.collection.objects.link(o)
    o.matrix_world = Matrix.Translation(loc) @ rot
for i in want:
    p = parts[i]; p.name = C.MESH
    for view, (loc, tgt, extra) in {'side': ((4, 0, 0.4), (0, 0, 0.4), ('WallYZ',)),
                                    'front': ((0, -4, 0.4), (0, 0, 0.4), ('WallXZ',)),
                                    'top': ((0, 0, 4), (0, 0, 0), ())}.items():
        C.render(loc, tgt, 2.3, os.path.join(HERE, 'review', f'piece{i}_{view}.png'), res=(1000, 1000), extra=extra)
        for o in bpy.data.objects:
            if o.type == 'MESH': o.hide_render = False
    p.name = f'part{i}'
