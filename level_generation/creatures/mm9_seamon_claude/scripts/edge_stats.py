"""Edge-length statistics of a GLB mesh and the faces with very long edges (sliver threads). Args: glb [factor]"""
import bpy, bmesh, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
fac = float(argv[1]) if len(argv) > 1 else 6
o = next(x for x in bpy.data.objects if x.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
L = np.array([e.calc_length() for e in bm.edges]); med = np.median(L)
print('EDGES', len(L), 'median', med, 'p99', np.percentile(L, 99), 'max', L.max())
long_f = [f for f in bm.faces if max(e.calc_length() for e in f.edges) > fac * med]
print('LONGFACES', len(long_f), [round(max(e.calc_length() for e in f.edges) / med, 1) for f in long_f[:40]])
cs = [f.calc_center_median() for f in long_f]
if cs:
    a = np.array([tuple(c) for c in cs]); print('LONGBOX', a.min(0).round(3), a.max(0).round(3))
