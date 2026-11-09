import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; mw = ob.matrix_world
names = {g.index: g.name for g in ob.vertex_groups}
for q in a[1].split(';'):
    p = Vector([float(t) for t in q.split(',')])
    best = sorted(ob.data.vertices, key=lambda v: ((mw @ v.co) - p).length)[:3]
    for v in best:
        print('WPROBE', v.index, [round(x, 4) for x in (mw @ v.co)], {names[g.group]: round(g.weight, 2) for g in v.groups if g.weight > 0.01})
