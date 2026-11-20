"""Diagnostic: joints carrying the head-set vertices (face attribute head = 1) of a master blend, by height band in the
Blender rest frame. Args (Blender): <blend>"""
import bpy, bmesh, sys
from collections import Counter, defaultdict
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); hl = bm.faces.layers.int.get('head')
hv = {v.index for f in bm.faces if f[hl] == 1 for v in f.verts}
names = [g.name for g in ob.vertex_groups]
band = defaultdict(Counter); share = defaultdict(lambda: defaultdict(float))
for i in hv:
    v = me.vertices[i]; z = round(v.co.z * 20) / 20
    tot = sum(g.weight for g in v.groups) or 1
    for g in v.groups:
        share[z][names[g.group]] += g.weight / tot
    dom = max(v.groups, key=lambda g: g.weight); band[z][names[dom.group]] += 1
for z in sorted(band):
    s = share[z]; n = sum(band[z].values())
    print('HEADW z %.2f n %4d ' % (z, n) + ', '.join(f'{k} {v / n:.2f}' for k, v in sorted(s.items(), key=lambda x: -x[1])[:5]))
