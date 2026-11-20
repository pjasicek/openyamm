"""Delete the hand-graft faces (attribute hand) that use a vertex within RADIUS of the given points (MM9 frame): HOF2's
right stub vertices inside the cuff that rose over it in Running/Death/Talk whatever their weights (sleeve_poke_gate).
The stub there is hidden inside the sleeve. Args: <in blend> <out blend> <x,y,z;...> [radius 0.008]"""
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
R = float(a[3]) if len(a) > 3 else 0.008
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; mw = ob.matrix_world
pts = [Vector([float(t) for t in q.split(',')]) for q in a[2].split(';')]
bm = bmesh.new(); bm.from_mesh(ob.data); lh = bm.faces.layers.int['hand']
dead = [f for f in bm.faces if f[lh] and any(any(((mw @ v.co) - p).length < R for p in pts) for v in f.verts)]
bmesh.ops.delete(bm, geom=dead, context='FACES')
bm.to_mesh(ob.data); ob.data.update()
print('DROP_FACES_NEAR', len(dead))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
