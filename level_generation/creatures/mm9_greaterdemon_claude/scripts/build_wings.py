"""Build the wings on the MM9 wing geometry and join them into the weighted 'Body'.

Args: <rig blend> <mm9 ground blend> <out blend> <report json> <config json>

Meshy built the wings in the frontal plane (as the masters show them from the front); MM9's wings sweep up and back,
and its flap clips move that geometry. So the wings are the MM9 wing faces themselves (faces whose three vertices are
dominated by the config 'wing_bones'): welded, duplicate back faces removed, subdivided (config 'cuts', flat, the
MM9 folds kept), then solidified into a thin closed shell (config 'thickness'). Weights are the barycentric blend of
the bones of the MM9 triangle under each vertex (the MM9 skin is rigid per vertex, so this is exactly the MM9
deformation, membrane stretch included). The wing vertices get piece 3 (reduce_body.py leaves them alone) and join
'Body'; the retexture paints them with the body.
"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
RIG, MM9, OUT, REP, CFGF = argv
cfg = json.load(open(CFGF))
WB = set(cfg['wing_bones'])
CUTS = cfg.get('cuts', 2)
THICK = cfg.get('thickness', 0.012)

bpy.ops.wm.open_mainfile(filepath=RIG)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
with bpy.data.libraries.load(MM9) as (src, dst):
    dst.objects = [n for n in src.objects if n != 'MM9_Rig']
mm9 = [o for o in dst.objects if o is not None and o.type == 'MESH']
for o in mm9:
    bpy.context.scene.collection.objects.link(o)
    o.parent = None
bm = bmesh.new()
tri_bones = []   # per source triangle: three (bone) names
pos = []
for o in mm9:
    me = o.data
    vg = {g.index: g.name for g in o.vertex_groups}
    dom = [vg[max(v.groups, key=lambda g: g.weight).group] if v.groups else None for v in me.vertices]
    for p in me.polygons:
        if len(p.vertices) != 3 or not all(dom[i] in WB for i in p.vertices):
            continue
        tri_bones.append([dom[i] for i in p.vertices])
        pos.append([tuple(o.matrix_world @ me.vertices[i].co) for i in p.vertices])
rep = {'mm9_wing_tris': len(pos)}
# sheet: welded triangles, duplicates (two-sided copies) removed
verts = {}
faces = set()
src_tris = []
for tri, bn in zip(pos, tri_bones):
    ids = []
    for c in tri:
        key = tuple(round(x, 4) for x in c)
        if key not in verts:
            verts[key] = bm.verts.new(c)
        ids.append(verts[key])
    k = frozenset(id(v) for v in ids)
    if len(k) < 3 or k in faces:
        continue
    faces.add(k)
    try:
        bm.faces.new(ids)
        src_tris.append((tri, bn))
    except ValueError:
        pass
bm.verts.ensure_lookup_table()
rep['sheet_tris'] = len(bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
if CUTS:
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=CUTS, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
# source triangles for the weights
tri_pts = [[Vector(c) for c in t] for t, _ in src_tris]
bvh = BVHTree.FromPolygons([tuple(p) for t in tri_pts for p in t],
                           [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(tri_pts))])
me = bpy.data.meshes.new('Wings')
bm.to_mesh(me)
wings = bpy.data.objects.new('Wings', me)
bpy.context.scene.collection.objects.link(wings)
bpy.context.view_layer.objects.active = wings
for o in bpy.data.objects:
    o.select_set(o == wings)
mod = wings.modifiers.new('solid', 'SOLIDIFY')
mod.thickness = THICK
mod.offset = 0.0
mod.use_rim = True
mod.use_even_offset = True
bpy.ops.object.modifier_apply(modifier='solid')
bones = sorted({b for _, bn in src_tris for b in bn})
for b in bones:
    wings.vertex_groups.new(name=b)
for v in wings.data.vertices:
    loc, nrm, fi, d = bvh.find_nearest(v.co)
    t = tri_pts[fi]
    w = {}
    # barycentric coordinates of loc in triangle t
    a, b_, c = t
    v0, v1, v2 = b_ - a, c - a, loc - a
    d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1)
    d20, d21 = v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-12:
        bc = (1 / 3, 1 / 3, 1 / 3)
    else:
        l1 = (d11 * d20 - d01 * d21) / den
        l2 = (d00 * d21 - d01 * d20) / den
        bc = (1 - l1 - l2, l1, l2)
    bc = [max(0.0, x) for x in bc]
    s = sum(bc) or 1.0
    for bn, x in zip(src_tris[fi][1], bc):
        w[bn] = w.get(bn, 0.0) + x / s
    for bn, x in w.items():
        if x > 0.005:
            wings.vertex_groups[bn].add([v.index], x, 'REPLACE')
for p in wings.data.polygons:
    p.use_smooth = False
rep['wing_tris'] = len(wings.data.polygons)
# attributes as on the body, then join
for nm, val in (('piece', 3), ('side', 0)):
    a = wings.data.attributes.new(nm, 'INT', 'POINT')
    for i, v in enumerate(wings.data.vertices):
        a.data[i].value = val if nm == 'piece' else (0 if abs(v.co.x) < 0.04 else (1 if v.co.x > 0 else -1))
for o in mm9:
    bpy.data.objects.remove(o)
if 'bone' in body.data.color_attributes:
    col = wings.data.color_attributes.new('bone', 'FLOAT_COLOR', 'POINT')
    for i in range(len(wings.data.vertices)):
        col.data[i].color = (0.2, 0.2, 0.9, 1)
wings.parent = arm
for o in bpy.data.objects:
    o.select_set(o in (body, wings))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
rep['body_tris'] = sum(len(p.vertices) - 2 for p in body.data.polygons)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('WINGS ' + json.dumps(rep))
