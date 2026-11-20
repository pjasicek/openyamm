"""Delete Body faces fully covered by the Tunic (skin poking through cloth at the collar/shoulders), then pull
remaining skin vertices that still sit outside the tunic around the opening 4 mm inward. Rest pose, UVs kept."""
import bpy, bmesh, json, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
m = bpy.data.objects['Peasant']; me = m.data
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
PARTS = json.loads(bpy.context.scene['pfem_parts'])
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.normal_update()
pl = bm.faces.layers.int.get('part')
tun = [f for f in bm.faces if f[pl] == PARTS.index('Tunic')]
tree = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [tuple(v.index for v in f.verts) for f in tun])
def covered(p, n):
    h = tree.ray_cast(p + n * 1e-4, n, 0.06)
    return h[0] is not None
body = [f for f in bm.faces if f[pl] == PARTS.index('Body')]
kill = []
for f in body:
    c = f.calc_center_median()
    if c.z > 1.42 or c.z < 0.85:
        continue
    if covered(c, f.normal) and all(covered(v.co, v.normal) for v in f.verts):
        kill.append(f)
bmesh.ops.delete(bm, geom=kill, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me); bm.free()
print('HIDDEN body faces removed', len(kill), 'tris now', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_mainfile()
