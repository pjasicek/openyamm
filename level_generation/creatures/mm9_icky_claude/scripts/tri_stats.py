"""Triangles of 'Body' by piece and by dominant bone group (top 12). Args: blend"""
import bpy, sys
from collections import Counter
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob = bpy.data.objects['Body']; me = ob.data
pc = me.attributes['piece']
names = {g.index: g.name for g in ob.vertex_groups}
byp, byb = Counter(), Counter()
for p in me.polygons:
    t = len(p.vertices) - 2
    byp[pc.data[p.vertices[0]].value] += t
    v = me.vertices[p.vertices[0]]
    g = max(v.groups, key=lambda g: g.weight) if len(v.groups) else None
    byb[names.get(g.group, '-') if g else '-'] += t
print('TRIS', dict(byp), byb.most_common(12))
