import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
me = bpy.data.objects['Body'].data
P = np.array([v.co[:] for v in me.vertices]); fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
pa = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: pa[v] = fp[p.index]
f = P[pa == 20]; h = P[pa == 21]
fr = f[(np.abs(f[:, 0]) < 0.01) & (f[:, 1] < -0.03)]
o = np.argsort(fr[:, 2])
print('PR midline front profile (z, y):', [(round(float(fr[i, 2]), 3), round(float(fr[i, 1]), 3)) for i in o][::4])
bk = f[(np.abs(f[:, 0]) < 0.01) & (f[:, 1] > 0.0)]
print('PR midline back face shell (z,y):', [(round(float(z), 3), round(float(y), 3)) for z, y in sorted(zip(bk[:, 2], bk[:, 1]))][::4])
print('PR hair z range', h[:, 2].min().round(3), h[:, 2].max().round(3), 'hair below .65 count', int((h[:, 2] < 0.65).sum()))
print('PR face bottom ring z', f[:, 2].min().round(3))
t = P[pa == 1]; print('PR tunic top', t[:, 2].max().round(3))
