import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob = bpy.data.objects['Dfly']; me = ob.data
HEAD = {ob.vertex_groups[n].index for n in ('Xheadpiv', 'Xhead', 'Xjawpiv')}
pc = me.attributes['piece']
c = {}
for p in me.polygons:
    pcs = max(pc.data[i].value for i in p.vertices)
    hw = sum(sum(g.weight for g in me.vertices[i].groups if g.group in HEAD) for i in p.vertices) / len(p.vertices)
    k = {1: 'eyes', 2: 'teeth/jaw pieces'}.get(pcs, 'head skin' if hw >= 0.5 else 'body')
    c[k] = c.get(k, 0) + len(p.vertices) - 2
print('BREAKDOWN', c, 'wings', len(bpy.data.objects['Dfly_Wings'].data.polygons))
