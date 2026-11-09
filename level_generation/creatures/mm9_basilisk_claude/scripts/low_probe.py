"""Lowest vertices of 'Body' (piece, chain, position) and per chain the min z. Args: <blend>"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me = bpy.data.objects['Body'].data
pc = me.attributes['piece'].data; ch = me.attributes['chain'].data
vs = sorted(me.vertices, key=lambda v: v.co.z)
for v in vs[:12]:
    print('LOW', v.index, pc[v.index].value, ch[v.index].value, tuple(round(c, 3) for c in v.co))
mins = {}
for v in me.vertices:
    k = (pc[v.index].value, ch[v.index].value)
    mins[k] = min(mins.get(k, 9), v.co.z)
print('MINS', sorted((k, round(z, 3)) for k, z in mins.items()))
