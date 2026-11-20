"""Blender: dump world-space bind-pose vertices (and skin joint of max weight) of every mesh in a GLB to npz.
Args: glb out.npz"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
P = []; G = []; N = []
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    names = [g.name for g in o.vertex_groups]
    for v in o.data.vertices:
        P.append(tuple(o.matrix_world @ v.co))
        g = max(v.groups, key=lambda g: g.weight, default=None)
        G.append(names[g.group] if g else '')
        N.append(o.name)
np.savez(a[1], P=np.array(P), G=np.array(G), N=np.array(N))
print('DUMP', len(P))
