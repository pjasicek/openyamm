"""Print the face-skin faces near a point with their normals and vertices (analysis for chin_fold.py). Args: <blend> <x> <y> <z> <r>"""
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); c = Vector([float(x) for x in a[1:4]]); r = float(a[4])
me = bpy.data.objects['Body'].data; bm = bmesh.new(); bm.from_mesh(me); bm.normal_update()
lp = bm.faces.layers.int['part']
for f in bm.faces:
    if f[lp] == 20 and (f.calc_center_median() - c).length < r:
        print('PCHIN f', f.index, 'n', [round(x, 2) for x in f.normal], 'area', round(f.calc_area() * 1e6, 2), 'v', [(v.index, [round(x * 1000, 1) for x in v.co]) for v in f.verts])
