"""Join the reduced voxel body (work/voxel_body_reduced.npz) with the mirrored eyes, fangs and claws and the
procedural tail (work/clean_parts.blend). Face attribute `part`: 0 body, 1 eyes, 2 fangs, 3 claws, 4 tail.
Reports the body's mirror error and boundary edges. Writes work/clean_v2.blend (object Saber)."""
import bpy, bmesh, os
import numpy as np
from mathutils import kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_parts.blend'))
R = np.load(os.path.join(HERE, 'work', 'voxel_body_reduced.npz'))
bme = bpy.data.meshes.new('Body'); bme.from_pydata(R['co'].tolist(), [], R['tris'].tolist()); bme.update()
body = bpy.data.objects.new('Body', bme); bpy.context.scene.collection.objects.link(body)
me = body.data
co = np.array([v.co[:] for v in me.vertices])
kd = kdtree.KDTree(len(co))
for i, c in enumerate(co): kd.insert(c, i)
kd.balance()
err = np.array([kd.find((-c[0], c[1], c[2]))[2] for c in co])
b = bmesh.new(); b.from_mesh(me)
print('BODY tris', len(me.polygons), 'boundary', sum(1 for e in b.edges if e.is_boundary),
      'nonmanifold', sum(1 for e in b.edges if not e.is_manifold), 'mirror err mm p50/p99/max',
      np.round(np.percentile(err, [50, 99, 100]) * 1000, 2))
b.free()
# soften the fused ruff edge on the chest, the flank dents and the tail-cut cap (fan caps under the voxel surface)
bs = bmesh.new(); bs.from_mesh(me)
REGIONS = [((-0.40, 0.40), (-0.95, -0.50), (0.30, 0.95)), ((-0.40, 0.40), (-0.15, 0.20), (0.55, 0.95)),
           ((-0.20, 0.20), (0.36, 0.55), (0.70, 1.10))]
sel = [v for v in bs.verts if any(r[0][0] <= v.co.x <= r[0][1] and r[1][0] <= v.co.y <= r[1][1] and
                                 r[2][0] <= v.co.z <= r[2][1] for r in REGIONS)]
for k in range(16):                       # Taubin smoothing (no shrink)
    f = 0.5 if k % 2 == 0 else -0.53
    new = {v: v.co + (sum((e.other_vert(v).co for e in v.link_edges), v.co * 0) / len(v.link_edges) - v.co) * f
           for v in sel}
    for v, c in new.items(): v.co = c
print('SMOOTHED verts', len(sel))
bs.to_mesh(me); bs.free()
a = me.attributes.new('part', 'INT', 'FACE')
for i in range(len(me.polygons)):
    a.data[i].value = 0
for o in bpy.data.objects: o.select_set(o.type == 'MESH')
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.name = body.data.name = 'Saber'
me = body.data
for nm in ('rank',):
    if nm in me.attributes: me.attributes.remove(me.attributes[nm])
for p in me.polygons:
    p.use_smooth = True
counts = {}
for p in me.polygons:
    v = me.attributes['part'].data[p.index].value; counts[v] = counts.get(v, 0) + 1
co = np.array([v.co[:] for v in me.vertices])
print('CLEAN tris', len(me.polygons), 'by part', dict(sorted(counts.items())), 'min', np.round(co.min(0), 3),
      'max', np.round(co.max(0), 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
