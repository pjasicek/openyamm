"""Crotch height (first surface hit by upward rays at x=0 over a few y) and shoulder (armpit) height for MM9 (no staff)
and our mesh. Args: <mm9 glb> <meshy glb>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
def load(p, skip=()):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    dg = bpy.context.evaluated_depsgraph_get(); bm = bmesh.new()
    for o in bpy.context.scene.objects:
        if o.type == 'MESH' and not any(o.name.startswith(s) for s in skip):
            m = o.evaluated_get(dg).to_mesh(); t = bmesh.new(); t.from_mesh(m); t.transform(o.matrix_world)
            tm = bpy.data.meshes.new('t'); t.to_mesh(tm); bm.from_mesh(tm)
    return bm
for nm, p, skip in (('MM9', a[0], ('staff', 'Icosphere')), ('OURS', a[1], ())):
    bm = load(p, skip); bvh = BVHTree.FromBMesh(bm)
    co = np.array([v.co for v in bm.verts]); z0 = co[:, 2].min(); H = np.ptp(co[:, 2])
    hits = []
    for y in np.linspace(-0.05, 0.05, 11) * H:
        h = bvh.ray_cast(Vector((0, y, z0 - 0.1)), Vector((0, 0, 1)))
        if h[0] is not None:
            hits.append(h[0].z - z0)
    # armpit: lowest z where the arm meets the torso side: upward rays at x = +-0.2 H .. scan inward
    arm = []
    for x in np.linspace(0.12, 0.25, 14) * H:
        for s in (-1, 1):
            h = bvh.ray_cast(Vector((s * x, 0, z0 + 0.5 * H)), Vector((0, 0, 1)))
            if h[0] is not None:
                arm.append((round(float(x / H), 3), s, round(float(h[0].z - z0) / H, 3)))
    print('CROTCH', nm, 'H', round(H, 3), 'crotch above soles', np.round(sorted(hits)[:3], 3), 'frac', round(min(hits) / H, 3))
    print('ARM', nm, arm)
