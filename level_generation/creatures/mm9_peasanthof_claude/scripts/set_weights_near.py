"""Set the weights of vertices within RADIUS of given points (MM9 frame) to fixed bone weights (HOF2: one right-wrist stub
vertex rose 27 mm over the cuff in Running/Death). Args: <in> <out> <x,y,z;...> <radius> <bone=w,bone=w>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; mw = ob.matrix_world
pts = [Vector([float(t) for t in q.split(',')]) for q in a[2].split(';')]
R = float(a[3]); W = {k: float(v) for k, v in (x.split('=') for x in a[4].split(','))}
n = 0
for v in ob.data.vertices:
    p = mw @ v.co
    if any((p - q).length < R for q in pts):
        for g in list(v.groups): ob.vertex_groups[g.group].remove([v.index])
        for b, w in W.items(): ob.vertex_groups[b].add([v.index], w, 'REPLACE')
        n += 1
print('SETWEIGHTS', n)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
