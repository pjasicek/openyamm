"""Relax 'Body' vertices within R of given points (Meshy folds: a pit in the right cheek, a notch in the back hair).
Positions only (before the UV pass). Args: <in blend> <out blend> <x,y,z,r;x,y,z,r...> [iterations 8]"""
import bpy, bmesh, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
its = int(argv[3]) if len(argv) > 3 else 8
for spec in argv[2].split(';'):
    x, y, z, r = (float(t) for t in spec.split(','))
    c = Vector((x, y, z))
    sel = [v for v in bm.verts if (v.co - c).length < r]
    for _ in range(its):
        new = {}
        for v in sel:
            nb = [e.other_vert(v).co for e in v.link_edges]
            if nb:
                w = max(0.0, 1 - (v.co - c).length / r)
                new[v] = v.co.lerp(sum(nb, Vector()) / len(nb), 0.6 * w)
        for v, p in new.items():
            v.co = p
    print('SMOOTHED', spec, len(sel))
bm.to_mesh(me); me.update()
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
