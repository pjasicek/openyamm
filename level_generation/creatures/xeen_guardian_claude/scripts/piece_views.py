"""Clay views of work/clean_v1.blend split into its connected pieces (random colour per piece), plus each listed piece
alone. Usage: piece_views.py [piece ...]  -> review/pieces_<view>.png, review/piece<k>_<view>.png"""
import bpy, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
mesh = bpy.data.objects['Skull']
label = np.load(os.path.join(HERE, 'work', 'pieces.npy'))
for v in mesh.data.vertices:
    v.select = False
attr = mesh.data.attributes.new('piece', 'INT', 'POINT')
attr.data.foreach_set('value', label.astype(np.int32))
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
parts = {}
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Floor':
        k = int(o.data.attributes['piece'].data[0].value); o.name = f'P{k}'; parts[k] = o
sc = bpy.context.scene
VIEWS = {'front': ((0, -3, 0.4), (0, 0, 0.4)), 'side': ((3, 0, 0.4), (0, 0, 0.4)),
         'quarter': ((-1.8, -2.2, 1.3), (0, 0, 0.4)), 'back': ((0, 3, 0.4), (0, 0, 0.4)),
         'under': ((0, -0.6, -3), (0, -0.1, 0.4))}
for view, (loc, tgt) in VIEWS.items():
    C.COLOR_OVERRIDE = 'RANDOM'
    C.render(loc, tgt, 1.0, os.path.join(HERE, 'review', f'pieces_{view}.png'), res=(600, 600), floor=False,
             extra=[o.name for o in parts.values()])
    C.COLOR_OVERRIDE = None
for k in argv:
    k = int(k)
    for view in ('front', 'side', 'back'):
        loc, tgt = VIEWS[view]
        C.render(loc, tgt, 1.0, os.path.join(HERE, 'review', f'piece{k}_{view}.png'), res=(500, 500), floor=False,
                 extra=[f'P{k}'])
print('PIECE VIEWS', sorted(parts))
