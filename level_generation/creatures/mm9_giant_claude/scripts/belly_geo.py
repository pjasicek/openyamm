"""Meshy put a disc on the belly (the master's belt boss, higher than the belt it painted): the bump is relaxed flat, vertex
positions only (UVs, weights frozen). Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
def w(v):
    x, y, z = v.co
    e = (x / 0.15) ** 2 + ((z - 0.335) / 0.17) ** 2
    return (y < -0.18) * float(np.clip((1.0 - e) / 0.25, 0, 1))
sel = [(v, w(v)) for v in bm.verts if w(v) > 0]
y0 = {v: v.co.y for v, _ in sel}
for it in range(60):
    new = {}
    for v, k in sel:
        nb = [e.other_vert(v).co for e in v.link_edges]
        c = sum(nb, v.co * 0) / len(nb)
        new[v] = v.co.lerp(c, 0.5 * k)
    for v, c in new.items(): v.co = c
mv = max(abs(v.co.y - y0[v]) for v, _ in sel)
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('BELLY verts', len(sel), 'max move cm', round(mv * 100, 2))
