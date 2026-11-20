"""Share of each piece's faces whose normal points away from the body axis (inverted shells). Args: -- <blend> piece ..."""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
me = bpy.data.objects['Body'].data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
for p in [int(x) for x in a[1:]]:
    fs = [f for f in me.polygons if pv[f.vertices[0]] == p]
    out = [float(np.dot(np.array(f.normal)[:2], np.array(f.center)[:2] - np.array([0, 0.02]))) for f in fs]
    print('NORMALS piece', p, 'faces', len(fs), 'outward share', round(float(np.mean(np.array(out) > 0)), 2))
