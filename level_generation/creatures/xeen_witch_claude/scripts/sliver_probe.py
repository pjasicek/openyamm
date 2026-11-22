"""List sliver faces (aspect) of P00 by region. Args: -- <aspect>"""
import bpy, bmesh, os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
asp = float(sys.argv[sys.argv.index('--') + 1])
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st_v1_parts.blend'))
o = bpy.data.objects['P00']
bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
rows = []
for f in bm.faces:
    vs = [v.co for v in f.verts]
    es = [(vs[i] - vs[(i + 1) % len(vs)]).length for i in range(len(vs))]
    area = f.calc_area()
    L = max(es); hgt = 2 * area / L if L > 0 else 0
    if hgt > 0 and L / hgt > asp and L > 0.03:
        c = f.calc_center_median()
        rows.append([f.index, round(L, 3), round(L / hgt, 1)] + [round(x, 3) for x in c])
for r in sorted(rows, key=lambda r: r[5]):
    print('SLIV', r)
