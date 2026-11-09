"""Torso half-width / depth per height, ours (Body in a blend) vs MM9's mesh (bind). Central cluster only (arms split off by gaps).
Args: <blend> <mm9 glb>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']
P = np.array([body.matrix_world @ v.co for v in body.data.vertices])
ex = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=a[1])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE' and o not in ex)
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
Q = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in ex and o.name.startswith('Box06'):
        e = o.evaluated_get(dg); m = e.to_mesh(); Q += [np.array(o.matrix_world @ v.co) for v in m.vertices]; e.to_mesh_clear()
Q = np.array(Q)
def cl(X, z, h=0.04):
    s = X[np.abs(X[:, 2] - z) < h]
    if len(s) < 3: return None
    xs = np.sort(s[:, 0]); gaps = np.diff(xs)
    # central cluster around x = 0
    lo = 0; hi = len(xs) - 1
    i0 = np.searchsorted(xs, 0)
    l = i0 - 1
    while l > 0 and gaps[l - 1] < 0.06: l -= 1
    r = i0
    while r < len(xs) - 1 and gaps[r] < 0.06: r += 1
    c = s[(s[:, 0] >= xs[max(l, 0)]) & (s[:, 0] <= xs[min(r, len(xs) - 1)])]
    return xs[max(l, 0)], xs[min(r, len(xs) - 1)], c[:, 1].min(), c[:, 1].max()
print('MM9 bounds', Q.min(0).round(3), Q.max(0).round(3), 'ours', P.min(0).round(3), P.max(0).round(3))
for z in np.arange(-0.95, 1.0, 0.1):
    A = cl(P, z); B = cl(Q, z)
    f = lambda r: 'none' if r is None else f'x {r[0]:+.2f}..{r[1]:+.2f} y {r[2]:+.2f}..{r[3]:+.2f}'
    print(f'SLICE z {z:+.2f}  ours {f(A)}   mm9 {f(B)}')
