"""Apply the master's reshape moves to a texturing upload (positions only; UVs/faces untouched): each upload vertex takes
the inverse-distance mean move of its 4 nearest ORIGINAL master vertices (the upload is the master's unposed geometry).
Args (Blender): <out upload glb> <in upload glb> <report json> <move.npy> [<move.npy> ...] (each [co_before | move])"""
import bpy, sys, json
import numpy as np
from mathutils import kdtree, Vector
a = sys.argv[sys.argv.index('--') + 1:]
OUT, IN, REP, moves = a[0], a[1], a[2], a[3:]
first = np.load(moves[0]); co0 = first[:, :3]; tot = np.zeros_like(co0)
for m in moves:
    arr = np.load(m); tot += arr[:, 3:]
t = kdtree.KDTree(len(co0))
for i, x in enumerate(co0): t.insert(Vector(x), i)
t.balance()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
o = next(x for x in bpy.data.objects if x.type == 'MESH'); me = o.data
mw = o.matrix_world; inv = mw.inverted()
dmax = 0.0; moved = 0
for v in me.vertices:
    w = mw @ v.co
    hits = t.find_n(w, 4)
    ds = np.array([h[2] for h in hits]); ids = [h[1] for h in hits]
    dmax = max(dmax, ds[0])
    g = 1.0 / np.maximum(ds, 1e-5) ** 2
    mv = (tot[ids] * g[:, None]).sum(0) / g.sum()
    if np.linalg.norm(mv) > 1e-5: moved += 1
    v.co = inv @ (w + Vector(mv))
me.update()
rep = dict(vertices=len(me.vertices), moved=moved, nearest_max_mm=dmax * 1000, move_max_cm=float(np.linalg.norm(tot, axis=1).max() * 100))
json.dump(rep, open(REP, 'w'), indent=1); print('MOVEUP', rep)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_materials='NONE', export_texcoords=True, export_normals=True)
