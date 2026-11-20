"""List sliver faces (longest edge > MINLEN m, min height < 3 mm) per piece of the step1 mesh. Args: -- <blend>"""
import bpy, sys, os
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
ob = bpy.data.objects['Body']; me = ob.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(v.co) for v in me.vertices])
MINLEN = float(os.environ.get('MINLEN', '0.04'))
out = {}
for p in me.polygons:
    vs = list(p.vertices); P = co[vs]
    e = [np.linalg.norm(P[i] - P[(i + 1) % len(vs)]) for i in range(len(vs))]
    L = max(e); h = 2 * p.area / L if L > 0 else 0
    if L > MINLEN and h < 0.003:
        out.setdefault(int(pv[vs[0]]), []).append((round(L, 3), [round(x, 3) for x in P.mean(0)]))
for k, v in sorted(out.items()):
    print('SPIKES piece', k, len(v), sorted(v, reverse=True)[:6])
