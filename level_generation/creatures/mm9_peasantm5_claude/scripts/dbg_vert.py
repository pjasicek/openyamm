import bpy, sys
import numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
b = bpy.data.objects['Body']; me = b.data; mw = b.matrix_world
tgt = Vector((0.5742, -0.0854, 1.0701 - 0.8535))
ha = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', ha)
he = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', he)
best = sorted(((mw @ v.co - tgt).length, v.index) for v in me.vertices)[:3]
for d, i in best:
    fs = [p.index for p in me.polygons if i in p.vertices]
    print('DBG', round(d, 4), i, tuple(round(x, 4) for x in (mw @ me.vertices[i].co)), 'faces hand', [int(ha[f]) for f in fs], 'head', [int(he[f]) for f in fs],
          'groups', sorted(((b.vertex_groups[g.group].name, round(g.weight, 2)) for g in me.vertices[i].groups), key=lambda x: -x[1])[:4])
