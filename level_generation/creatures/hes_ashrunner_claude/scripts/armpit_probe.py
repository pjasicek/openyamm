"""Where the arms part from the torso shell (garment 1): connected components of the garment-1 vertices below z, for
a range of z, with each component's vertex count and x range. Args: -- <blend>"""
import bpy, sys, os
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
me = bpy.data.objects['Body'].data
co = np.array([v.co[:] for v in me.vertices]); gv = np.array([a.value for a in me.attributes['garment'].data])
E = np.array([e.vertices[:] for e in me.edges])
for z in np.arange(1.05, 1.36, 0.025):
    low = (gv == 1) & (co[:, 2] < z)
    par = np.arange(len(co))
    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for i, j in E:
        if low[i] and low[j]:
            a, b = f(i), f(j)
            if a != b:
                par[a] = b
    roots = {}
    for i in np.where(low)[0]:
        roots.setdefault(f(i), []).append(i)
    comps = sorted(roots.values(), key=len, reverse=True)[:5]
    print('ARMPIT z', round(float(z), 3), [(len(c), round(float(co[c, 0].min()), 2), round(float(co[c, 0].max()), 2)) for c in comps])
