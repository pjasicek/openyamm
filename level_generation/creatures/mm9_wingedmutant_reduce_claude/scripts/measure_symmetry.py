"""Mirror symmetry in the rest pose (rework 2026-10-30): for every vertex of the LOD0 body mesh (wings included) the
distance to the nearest point of the mesh mirrored about x = 0 (glTF axis 0; MM9's symmetry plane), in % of the
largest bounding-box extent. Args: -- <glb|blend> [<glb|blend> ...]. Prints SYM <file> median p90 max (%)."""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
for f in sys.argv[sys.argv.index('--') + 1:]:
    if f.endswith('.blend'):
        bpy.ops.wm.open_mainfile(filepath=f)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=f)
    for a in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
        if a.animation_data:
            a.animation_data.action = None
        for pb in a.pose.bones:
            pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('Icosphere')
           and 'LOD' not in o.name.upper().replace('LOD0', '') and 'shadow' not in o.name.lower()]
    V, T = [], []
    for o in obs:
        me = o.data
        base = sum(len(v) for v in V)
        V.append(np.array([tuple(o.matrix_world @ v.co) for v in me.vertices]))
        T += [[base + i for i in p.vertices] for p in me.polygons]
    V = np.concatenate(V)
    M = V * np.array([-1, 1, 1])
    bvh = BVHTree.FromPolygons([Vector(p) for p in M], T)
    d = np.array([(Vector(p) - bvh.find_nearest(Vector(p))[0]).length for p in V])
    size = float(np.ptp(V, 0).max())
    from mathutils.kdtree import KDTree
    kd = KDTree(len(M))
    for i, p in enumerate(M):
        kd.insert(Vector(p), i)
    kd.balance()
    dv = np.array([kd.find(Vector(p))[2] for p in V])
    print('SYMV', os.path.basename(f), 'vertex-to-mirrored-vertex median %.2f p90 %.2f max %.2f %%' % tuple(
        100 * np.array([np.median(dv), np.percentile(dv, 90), dv.max()]) / size))
    print('SYM', os.path.basename(f), [o.name for o in obs], 'verts', len(V), 'median %.2f p90 %.2f max %.2f %%' % tuple(
        100 * np.array([np.median(d), np.percentile(d, 90), d.max()]) / size))
