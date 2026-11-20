"""Legs restored under the skirt (user review 2026-10-20, batch J m312's dress route): the body retexture was painted on
the earlier mesh without legs, so the leg faces (garment 15 above the shoe tops, rest z > TOP) get every corner's UVMap
coordinate set to the centroid of the largest petticoat face (piece 2): white linen stockings, hidden by the skirt
except in the corpse and at the hem. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
TOP = float(os.environ.get('LEG_TOP', '0.12'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data
gv = np.array([a.value for a in me.attributes['garment'].data]); pv = np.array([a.value for a in me.attributes['piece'].data])
co = np.array([v.co[:] for v in me.vertices]); uv = me.uv_layers['UVMap'].data
pet = max((p for p in me.polygons if pv[p.vertices[0]] == 2), key=lambda p: p.area)
c = np.mean([tuple(uv[l].uv) for l in pet.loop_indices], 0)
n = 0
for p in me.polygons:
    vs = list(p.vertices)
    if gv[vs[0]] == 15 and co[vs, 2].mean() > TOP:
        for l in p.loop_indices:
            uv[l].uv = (float(c[0]), float(c[1]))
        n += 1
print('LEGSUV faces', n, 'uv', np.round(c, 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
