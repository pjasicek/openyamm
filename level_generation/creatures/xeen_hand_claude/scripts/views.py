"""Clay views of a blend's Hand (review/<prefix>_*.png). Args: -- <blend in work/> <prefix> [random] [parts] [close]"""
import bpy, os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
if 'random' in a:
    C.COLOR_OVERRIDE = 'RANDOM'
ob = bpy.data.objects['Hand']
if 'parts' in a:
    pa = np.zeros(len(ob.data.polygons), np.int32); ob.data.attributes['part'].data.foreach_get('value', pa)
    cols = [(0.78, 0.6, 0.45), (0.9, 0.5, 0.4), (0.5, 0.05, 0.05), (0.85, 0.2, 0.25), (0.85, 0.85, 0.8),
            (0.3, 0.5, 0.9), (0.3, 0.8, 0.4)]
    ob.data.materials.clear()
    for c in cols:
        m = bpy.data.materials.new('m'); m.diffuse_color = (*c, 1); ob.data.materials.append(m)
    for p in ob.data.polygons: p.material_index = int(pa[p.index])
    C.COLOR_OVERRIDE = 'MATERIAL'
if 'nolids' in a:
    import bmesh
    pa = np.zeros(len(ob.data.polygons), np.int32); ob.data.attributes['part'].data.foreach_get('value', pa)
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if pa[f.index] in (5, 6)], context='FACES')
    bm.to_mesh(ob.data); bm.free()
co = np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices])
c = (co.min(0) + co.max(0)) / 2; s = float((co.max(0) - co.min(0)).max()) * 1.15
views = {'front': (0, -5, 0), 'quarter': (-3, -3.5, 2), 'side': (-5, 0, 0), 'back': (0, 5, 0), 'top': (0, 0, 5)}
if 'close' in a:
    M = json.load(open(os.path.join(HERE, 'work', 'mouth.json')))
    c = np.array(M['O']); s = 0.26
    views = {'mfront': tuple(np.array(M['n']) * 5), 'mquarter': (2.5, -3.5, 2.5), 'mside': (-4, -3, 0.5)}
for name, d in views.items():
    C.render(tuple(c + np.array(d)), tuple(c), s, os.path.join(HERE, 'review', f'{a[1]}_{name}.png'), res=(600, 450),
             floor=False)
