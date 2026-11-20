"""Pull hand-graft vertices within RADIUS of the given points (MM9 frame, rest) radially toward the forearm axis of their
side to K x their distance (HOF2: right-stub vertices inside the cuff rose over it when the wrist bent; deleting them
opened the cuff, so they are tucked instead). Positions only. Args: <in> <out> <x,y,z;...> [radius 0.012] [k 0.55]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
R = float(a[3]) if len(a) > 3 else 0.012; K = float(a[4]) if len(a) > 4 else 0.55
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent; mw = ob.matrix_world; mwi = mw.inverted()
pts = [Vector([float(t) for t in q.split(',')]) for q in a[2].split(';')]
bm = bmesh.new(); bm.from_mesh(ob.data); lh = bm.faces.layers.int['hand']
n = 0
for v in bm.verts:
    p = mw @ v.co
    if not any(f[lh] for f in v.link_faces) or not any((p - q).length < R for q in pts): continue
    tok = 'R' if p.x > 0 else 'L'
    a0 = rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local
    a1 = rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local
    ax = (a1 - a0).normalized(); s = (p - a1).dot(ax); foot = a1 + ax * s
    v.co = mwi @ (foot + (p - foot) * K); n += 1
bm.to_mesh(ob.data); ob.data.update()
print('TUCK_POINTS', n)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
