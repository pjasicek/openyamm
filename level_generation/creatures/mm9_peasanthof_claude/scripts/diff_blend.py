import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
def load(p):
    bpy.ops.wm.open_mainfile(filepath=p)
    ob = bpy.data.objects['Body']; return [tuple(ob.matrix_world @ v.co) for v in ob.data.vertices]
A = load(a[0]); B = load(a[1])
import math
n = min(len(A), len(B))
for i in range(n):
    d = math.dist(A[i], B[i])
    if d > 1e-5: print('MOVED', i, [round(x, 4) for x in A[i]], '->', [round(x, 4) for x in B[i]])
