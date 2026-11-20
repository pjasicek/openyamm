"""Delete from a texturing upload the faces of the parts strip_parts.py removed from the master (ponytail, necklace beads,
eyeball cups): an upload face goes when the nearest face centre of the ORIGINAL master (same geometry, unposed) belongs
to a removed part. UVs of the kept faces are untouched (no re-layout: the paid paint maps by these UVs).
Args (Blender): <original master blend> <stripped master blend> <in upload glb> <out upload glb> <report json>"""
import bpy, sys, json
import numpy as np
from mathutils import kdtree


def query(points, q):
    t = kdtree.KDTree(len(points))
    for i, x in enumerate(points): t.insert(x, i)
    t.balance()
    r = [t.find(x) for x in q]
    return np.array([x[2] for x in r]), np.array([x[1] for x in r])
a = sys.argv[sys.argv.index('--') + 1:]
ORIG, STRIP, IN, OUT, REP = a


def centres(blend):
    bpy.ops.wm.open_mainfile(filepath=blend)
    body = bpy.data.objects['Body']; rig = body.parent
    if rig.animation_data: rig.animation_data.action = None
    for b in rig.pose.bones: b.matrix_basis.identity()
    bpy.context.view_layer.update()
    return np.array([body.matrix_world @ p.center for p in body.data.polygons])


C0 = centres(ORIG); C1 = centres(STRIP)
d, _ = query(C1, C0)
removed = d > 1e-5
print('master faces', len(C0), 'kept', len(C1), 'removed', int(removed.sum()))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
o = next(x for x in bpy.data.objects if x.type == 'MESH'); me = o.data
U = np.array([o.matrix_world @ p.center for p in me.polygons])
dist, idx = query(C0, U)
drop = removed[idx] & (dist < 0.004)
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if drop[f.index]], context='FACES')
bm.to_mesh(me); bm.free(); me.update()
rep = dict(upload_faces=len(U), dropped=int(drop.sum()), kept=len(me.polygons), match_p99_mm=float(np.percentile(dist, 99) * 1000),
           match_max_mm=float(dist.max() * 1000))
json.dump(rep, open(REP, 'w'), indent=1); print('STRIPUP', rep)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_materials='NONE', export_texcoords=True,
                          export_normals=True)
