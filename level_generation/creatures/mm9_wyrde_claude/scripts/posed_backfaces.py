"""Faces seen from behind in POSED frames of the export GLB (the fall and the corpse show linings the rest pose cannot): the LOD0 mesh is
posed at each clip:seconds, ray grids (STEP m) from 8 azimuths x the elevations; every back-face hit is written as the rest-pose
centroid of its polygon (Blender frame of the imported GLB) for linings_wy.py to map onto the frozen mesh.
Args: <glb> <out npy> <clip:sec,...> [step 0.004] [elev 0,20]"""
import bpy, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, items = a[0], a[1], a[2].split(','); STEP = float(a[3]) if len(a) > 3 else 0.004
ELEV = [float(x) for x in (a[4] if len(a) > 4 else '0,20').split(',')]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
lod0 = max((o for o in meshes if 'Shadow' not in o.name and 'LOD' not in o.name), key=lambda o: len(o.data.polygons), default=None) or max(meshes, key=lambda o: len(o.data.polygons))
print('LOD0', lod0.name, len(lod0.data.polygons))
me0 = lod0.data; rest = np.array([lod0.matrix_world @ v.co for v in me0.vertices])
cent = np.array([rest[list(p.vertices)].mean(0) for p in me0.polygons])
hits = {}
sc = bpy.context.scene
for it in items:
    clip, t = it.split(':'); act = next(x for x in bpy.data.actions if x.name.startswith(clip))
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
    fr = float(t) * sc.render.fps; sc.frame_set(int(fr), subframe=fr % 1.0); bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); ev = lod0.evaluated_get(dg); m = ev.to_mesh()
    P = [lod0.matrix_world @ v.co for v in m.vertices]; F = [tuple(p.vertices) for p in m.polygons]
    bvh = BVHTree.FromPolygons(P, F); Pn = np.array([tuple(p) for p in P])
    fn = np.array([tuple((P[f[1]] - P[f[0]]).cross(P[f[2]] - P[f[0]]).normalized()) for f in F])
    lo, hi = Pn.min(0), Pn.max(0); c = (lo + hi) / 2; R = np.linalg.norm(hi - lo) / 2 + 0.05; n = int(2 * R / STEP); k0 = len(hits)
    for el in ELEV:
        for az in range(0, 360, 45):
            th, ph = math.radians(az), math.radians(el)
            d = -np.array([math.sin(th) * math.cos(ph), -math.cos(th) * math.cos(ph), math.sin(ph)])
            u = np.cross(d, [0, 0, 1.0]); u /= np.linalg.norm(u); v = np.cross(u, d)
            for i in range(n):
                for j in range(n):
                    o = c - d * (R + 1) + u * (-R + i * STEP) + v * (-R + j * STEP)
                    loc, nor, fi, dist = bvh.ray_cast(Vector(o), Vector(d))
                    if fi is not None and fn[fi] @ d > 0: hits[fi] = hits.get(fi, 0) + 1
    ev.to_mesh_clear(); print('POSE', it, 'back-face polygons so far', len(hits))
idx = np.array(sorted(hits)); np.save(out, np.c_[cent[idx], [hits[i] for i in idx]]); print('POSED_BACKFACES', len(idx))
