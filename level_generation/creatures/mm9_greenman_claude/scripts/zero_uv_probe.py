"""Faces of 'Body' with zero UV area on UVMap: their 3D area and position. Args: <blend>"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data; uv = me.uv_layers['UVMap'].data
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
out = []
for p in me.polygons:
    if hd[p.index] or hn[p.index]: continue
    t = np.array([uv[l].uv[:] for l in p.loop_indices])
    ua = abs((t[1, 0]-t[0, 0])*(t[2, 1]-t[0, 1])-(t[2, 0]-t[0, 0])*(t[1, 1]-t[0, 1]))/2
    if ua < 1e-10: out.append((p.area, tuple(np.round(p.center, 3))))
ar = np.array([o[0] for o in out])
print('ZEROUV', len(out), 'area3d max %.2e sum %.2e' % (ar.max(), ar.sum()) if len(ar) else '', out[:8])
