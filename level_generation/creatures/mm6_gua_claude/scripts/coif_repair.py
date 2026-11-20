"""Coif and small-part repair on the Smart Topology return (work/st1_parts.blend -> work/st1r_parts.blend).

Meshy built the mail coif (P02) as a closed cylinder over the whole face, standing off the jaw like a bucket and
ending 3-5 cm above the shirt collar (bare neck visible). The native guard (and the HD masters) show an eye
opening under the helmet rim, the coif close around the jaw and running down into the mail shirt.

1. Delete the belt buckle shells (P07, P09-P11); the buckle comes from the texture.
2. Jaw hug: coif vertices below the eyes move toward the face/neck surface (P03) to a 12 mm stand-off,
   blended in over z 1.44 -> 1.40; never outward.
3. Eye window: coif faces in front of the eyes (z 1.403-1.452, |x| < 5.6 cm) removed; the window rim is extruded
   70 % of the way toward the face, so the opening has a visible mail thickness.
4. Collar: the coif's lower boundary is extruded down/outward until it is 6 mm inside the shirt (P00).
Landmarks from probe_head.py: helmet rim z 1.449, eyes ~1.415-1.425, nose tip 1.40, chin 1.34."""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st1_parts.blend'))
O = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
for n in ('P07', 'P09', 'P10', 'P11'):
    bpy.data.objects.remove(O.pop(n), do_unlink=True)


def tree(o):
    return BVHTree.FromPolygons([v.co.copy() for v in o.data.vertices], [p.vertices[:] for p in o.data.polygons])


face_t = tree(O['P03'])
shirt_t = tree(O['P00'])
NECK = Vector((-0.006, 0.05))          # head/neck axis in plan (x, y)


def smooth(t, a, b):
    return min(1.0, max(0.0, (t - a) / (b - a))) ** 2 * (3 - 2 * min(1.0, max(0.0, (t - a) / (b - a))))


bm = bmesh.new()
bm.from_mesh(O['P02'].data)
bm.verts.ensure_lookup_table()
# 2. jaw hug
moved = 0
for v in bm.verts:
    w = 1.0 - smooth(v.co.z, 1.40, 1.44)
    if w <= 0 or v.co.z < 1.31:
        continue
    loc, nrm, i, d = face_t.find_nearest(v.co)
    if loc is None:
        continue
    out = (v.co - loc)
    if out.length < 1e-6 or out.dot(nrm) < 0:          # inside the face: leave
        continue
    target = loc + out.normalized() * 0.012
    if (v.co - loc).length > 0.012:
        v.co = v.co.lerp(target, 0.85 * w)
        moved += 1
for _ in range(3):                                      # relax the pulled band
    new = {}
    for v in bm.verts:
        if 1.31 < v.co.z < 1.44 and not v.is_boundary:
            c = sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)
            new[v] = v.co.lerp(c, 0.4)
    for v, c in new.items():
        v.co = c
# 3. eye window
win = [f for f in bm.faces if 1.403 < f.calc_center_median().z < 1.452 and abs(f.calc_center_median().x + 0.006) < 0.056
       and f.calc_center_median().y < -0.004]
bmesh.ops.delete(bm, geom=win, context='FACES')
rim = [e for e in bm.edges if e.is_boundary and all(1.395 < v.co.z < 1.46 and v.co.y < 0.0 for v in e.verts)]
ext = bmesh.ops.extrude_edge_only(bm, edges=rim)
for v in [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]:
    loc, nrm, i, d = face_t.find_nearest(v.co)
    if loc is not None:
        v.co = v.co.lerp(loc, 0.7)
# 4. collar: extend the lower boundary into the shirt
bm.verts.ensure_lookup_table()
low = [e for e in bm.edges if e.is_boundary and all(v.co.z < 1.36 for v in e.verts)]
ext = bmesh.ops.extrude_edge_only(bm, edges=low)
miss = 0
for v in [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]:
    radial = Vector((v.co.x - NECK.x, v.co.y - NECK.y, 0))
    radial = radial.normalized() if radial.length > 1e-6 else Vector((0, -1, 0))
    d = (radial * 0.55 + Vector((0, 0, -1))).normalized()
    loc, nrm, i, dist = shirt_t.ray_cast(v.co + d * 0.002, d, 0.10)
    if loc is None:
        v.co = v.co + d * 0.03
        miss += 1
    else:
        v.co = loc + d * 0.006
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(O['P02'].data)
bm.free()
O['P02'].data.update()
print('COIF moved', moved, 'window faces', len(win), 'collar misses', miss)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'st1r_parts.blend'))
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.show_wire = False
sc = bpy.context.scene
common.workbench_clay(sc)
sc.display.shading.color_type = 'MATERIAL'
common.render_views(os.path.join(common.REVIEW, 'st1r_head'), 1.41, 0.34, views=('front', 'three_quarter', 'left', 'back'),
                    resolution=(500, 500))
