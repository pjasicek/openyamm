"""Chest diagnosis on work/uv_final.blend: open edges, faces whose normal points into the body, and a close render
coloured by face orientation (blue outward, red inward) plus the textured master."""
import os, math, bmesh, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'uv_final.blend'))
o = bpy.data.objects['Wyrm']
bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
tree = BVHTree.FromBMesh(bm)
open_e = [e for e in bm.edges if len(e.link_faces) == 1]
print('OPEN', len(open_e), [tuple(round(c, 3) for c in (e.verts[0].co + e.verts[1].co) / 2) for e in open_e if (e.verts[0].co.y < -0.25 and e.verts[0].co.z < 0.25)][:20])
# inward faces: ray along the normal from the face centre hits own mesh very close and the hit faces the same way
inward = []
for f in bm.faces:
    c = f.calc_center_median(); n = f.normal
    if not (-0.42 < c.y < -0.25 and c.z < 0.25):
        continue
    hit = tree.ray_cast(c + n * 1e-4, n, 0.08)
    if hit[0] is not None:
        hn = hit[1]
        if hn.dot(n) > 0.2:     # next surface along the normal faces the same way -> this face is inside
            inward.append(f.index)
print('INSIDE_FACES', len(inward), [tuple(round(x, 3) for x in bm.faces[i].calc_center_median()) for i in inward[:15]])
