"""Retexture master for the reduced thief (user 2026-10-14: "retexture the body; split one texture cloak (+ hood),
another the rest").

In:  ../mm6_thf_claude/work/rig_v3.blend (rig, the 2026-10-14 clips, full mesh with face attributes part / uv_region /
     head) and the accepted reduction Cand_45 (work/ladder.blend: weights by data transfer, the installed atlas UVs).
Out: work/master_tex.blend, texturing/thf_{cloak,body}_upload.glb (the body upload carries the whole thief, see
     below), work/master_tex.json.

Texture sets (face attribute `tex_set`): 1 cloak = the Cloak part (cloak, mantle, hood and their insides); 2 head = the
installed head set without the hood (face skin and hair; its texture is kept, cropped from the installed atlas);
0 body = everything else. Every reduced face takes part / uv_region / head from the nearest source face.
UVs: cloak and body get fresh layouts cut along the source's uv_region borders (the original chart plan), angle-based
unwrap (crushed closed shells re-unwrapped by smart projection), body islands sized by part weight and visibility
(weigh_islands), packed per set into 0..1; head
faces keep their installed UVs, remapped from the atlas's head half."""
import json
import os

import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
CRE = os.path.dirname(HERE)
ATLAS_W, HALF, GUTTER = 2080, 1024, 32          # installed merge_head_material atlas: body | gutter | head
BODY_FILL = 0.97                                # body islands in [0, 0.97]^2
# 'installed' (user 2026-10-14, after three body retextures smeared the belt and lower jerkin): the body faces keep
# the installed texture and UVs; 'new': a fresh weighted layout for a Meshy body retexture (texturing upload)
BODY_UVS = 'installed_col'
# 'installed_col' (user review 2026-10-14: holes in the jerkin; better, sharper daggers): the installed body texture
# and UVs (per-face island transfer, below), squeezed into u < DAGGER_COL[0] so the rebuilt daggers (dagger_mesh) get
# their own painted column. 'baked' (fresh layout + bake_body.py projection) was tried and dropped: the layered
# jerkin/shirt skirt and the installed radial skirt chart made the projection blur the lower jerkin.
DAGGER_COL = (0.925, 0.995)                     # u range of the dagger column in the body image
COL_FILL = DAGGER_COL[0] - 0.005                # installed body image squeezed into u < COL_FILL
CLOAK_FROM = os.path.join(HERE, 'work', 'ladder_r45_h70.blend')   # reduction the cloak texture belongs to
# body UVs: the decimation's own texture-aware UVs, except faces whose UV centroid lies more than TRANSFER_TOL from the
# per-face transfer from the full-detail mesh (a decimated face that slid into the neighbouring shirt chart: a green
# patch in the jerkin); the transfer alone stretched corners that fall off their island
DROP_HIDDEN = 0.95          # min source visibility `hid` over a face's vertices to remove it (0 = keep all)
BODY_TRANSFER = False      # tried with a centroid tolerance: the layered jerkin/shirt skirt broke more faces than it fixed
TRANSFER_TOL = 0.03
DAGGER_RECTS = {'blade': (0.40, 0.99), 'grip': (0.17, 0.38), 'iron': (0.01, 0.15)}   # v ranges
DUMMY = (0.978, 0.978, 0.018)                   # u0, v0, size: where the body upload's cloak/head faces go


def rest(rig):
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()


bpy.ops.wm.open_mainfile(filepath=os.path.join(CRE, 'mm6_thf_claude', 'work', 'rig_v3.blend'))
rig = bpy.data.objects['Thief_Rig']
rest(rig)
source = bpy.data.objects['Thief']
source.name = 'Source'
with bpy.data.libraries.load(os.path.join(HERE, 'work', 'ladder.blend')) as (src, dst):
    dst.objects = ['Cand_45']
mesh = dst.objects[0]
bpy.context.scene.collection.objects.link(mesh)
for o in [o for o in bpy.data.objects if o.name not in ('Thief_Rig', 'Source', mesh.name)]:
    bpy.data.objects.remove(o)
for a in [a for a in bpy.data.actions if '.' in a.name]:
    bpy.data.actions.remove(a)
mesh.parent = rig
mesh.matrix_world = source.matrix_world.copy()
mesh.hide_render = mesh.hide_viewport = False
for md in mesh.modifiers:
    if md.type == 'ARMATURE':
        md.object = rig
if 'ReduceProtect' in mesh.vertex_groups:
    mesh.vertex_groups.remove(mesh.vertex_groups['ReduceProtect'])

# --- face labels from the nearest source face ---------------------------------------------------------------------
sbm = bmesh.new()
sbm.from_mesh(source.data)
sbm.faces.ensure_lookup_table()
tree = BVHTree.FromBMesh(sbm)
labels = {n: [d.value for d in source.data.attributes[n].data] for n in ('part', 'uv_region', 'head')}
picked = []
for p in mesh.data.polygons:
    _, _, index, _ = tree.find_nearest(p.center)
    picked.append(index)
for n, values in labels.items():
    if n in mesh.data.attributes:
        mesh.data.attributes.remove(mesh.data.attributes[n])
    mesh.data.attributes.new(n, 'INT', 'FACE').data.foreach_set('value', [values[i] for i in picked])


def label(obj):
    """part / uv_region / head of each face of obj from the nearest source face."""
    near = [tree.find_nearest(p.center)[2] for p in obj.data.polygons]
    for n_, values in labels.items():
        if n_ in obj.data.attributes:
            obj.data.attributes.remove(obj.data.attributes[n_])
        obj.data.attributes.new(n_, 'INT', 'FACE').data.foreach_set('value', [values[i] for i in near])


# the cloak from the reduction its Meshy texture was made for (CLOAK_FROM); the rest from the current ladder (whose
# torso and skirt were reduced more gently: big triangles across the leather/shirt border showed the shirt colour as
# wedges in the jerkin, user review 2026-10-14). They share 3 vertices at the neck under the hood.
if os.path.exists(CLOAK_FROM):
    with bpy.data.libraries.load(CLOAK_FROM) as (src_c, dst_c):
        dst_c.objects = ['Cand_45']
    old = dst_c.objects[0]
    for o in [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name not in ('Thief_Rig',)]:
        bpy.data.objects.remove(o)
    for a in [a for a in bpy.data.actions if '.' in a.name]:
        bpy.data.actions.remove(a)
    bpy.context.scene.collection.objects.link(old)
    old.parent = rig
    old.matrix_world = mesh.matrix_world.copy()
    old.modifiers.clear()
    label(old)
    CLOAK = 1
    for obj, keep_cloak in ((mesh, False), (old, True)):
        b_ = bmesh.new()
        b_.from_mesh(obj.data)
        b_.faces.ensure_lookup_table()
        pl = b_.faces.layers.int['part']
        bmesh.ops.delete(b_, geom=[f for f in b_.faces if (f[pl] == CLOAK) != keep_cloak], context='FACES')
        bmesh.ops.delete(b_, geom=[v for v in b_.verts if not v.link_faces], context='VERTS')
        b_.to_mesh(obj.data)
        b_.free()
    for o in bpy.data.objects:
        o.select_set(o in (mesh, old))
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.join()
    picked = None
from mathutils import kdtree
kd = kdtree.KDTree(len(source.data.vertices))
for i, v in enumerate(source.data.vertices):
    kd.insert(v.co, i)
kd.balance()
src_hid = [d.value for d in source.data.attributes['hid'].data]
hid = [src_hid[kd.find(v.co)[1]] for v in mesh.data.vertices]
part = [d.value for d in mesh.data.attributes['part'].data]
region = [d.value for d in mesh.data.attributes['uv_region'].data]
head = [d.value for d in mesh.data.attributes['head'].data]
if BODY_UVS in ('baked', 'installed_col'):
    import dagger_mesh
    dagger_mesh.replace(mesh, rig, bpy.context.scene, part)
    part = [d.value for d in mesh.data.attributes['part'].data]
    region = [d.value for d in mesh.data.attributes['uv_region'].data]
    head = [d.value for d in mesh.data.attributes['head'].data]
    hid = [src_hid[kd.find(v.co)[1]] for v in mesh.data.vertices]
# never-seen inner layers (source `hid` ~ 1 on every vertex, e.g. the shirt under the jerkin skirt) are removed: after
# the reduction they poked through the jerkin as shirt-coloured patches (user review 2026-10-14)
if DROP_HIDDEN:
    bm_h = bmesh.new()
    bm_h.from_mesh(mesh.data)
    bm_h.faces.ensure_lookup_table()
    gone = [f for f in bm_h.faces if part[f.index] != 1 and min(hid[v.index] for v in f.verts) >= DROP_HIDDEN]
    bmesh.ops.delete(bm_h, geom=gone, context='FACES')
    bmesh.ops.delete(bm_h, geom=[v for v in bm_h.verts if not v.link_faces], context='VERTS')
    bm_h.to_mesh(mesh.data)
    bm_h.free()
    print('HIDDEN faces removed', len(gone))
    part = [d.value for d in mesh.data.attributes['part'].data]
    region = [d.value for d in mesh.data.attributes['uv_region'].data]
    head = [d.value for d in mesh.data.attributes['head'].data]
    hid = [src_hid[kd.find(v.co)[1]] for v in mesh.data.vertices]
PARTS_ALL = json.loads(bpy.context.scene['thf_parts'])
REGIONS_ALL = json.loads(bpy.context.scene['thf_uv_regions'])
# inner layers poking through after the reduction (user review 2026-10-14: a shirt-coloured patch in the jerkin; the
# double-sided body material shows such a face's back): a body face (not cloak, head or dagger) whose BACK is seen
# unobstructed from a viewpoint around the creature, level to 60 deg above (the game camera; from below the skirt's
# legitimate inside would count), is removed
import math as _m
bm_p = bmesh.new()
bm_p.from_mesh(mesh.data)
bm_p.faces.ensure_lookup_table()
ptree = BVHTree.FromBMesh(bm_p)
dirs = [Vector((_m.cos(az) * _m.cos(el), _m.sin(az) * _m.cos(el), _m.sin(el)))
        for el in (_m.radians(0), _m.radians(25), _m.radians(55)) for az in [k * 2 * _m.pi / 16 for k in range(16)]]
poke = []
LAYERED = {PARTS_ALL.index(n_) for n_ in ('Torso', 'Skirt')}   # the garments worn in layers (daggers, hands: open shells)
GRID = [(i / 7, j / 7) for i in range(8) for j in range(8 - i)]
ARMS = {REGIONS_ALL.index(n_) for n_ in ('ArmL', 'ArmR')}       # the sleeves are single shells: a removed face is a slit
for f in bm_p.faces:
    if part[f.index] not in LAYERED or head[f.index] == 1 or region[f.index] in ARMS:
        continue
    c = f.calc_center_median()
    # a barycentric grid over the face: intersecting layers stick out over part of a face only
    a_, b_, c_ = (v.co for v in f.verts[:3])
    pts = [a_ + (b_ - a_) * u + (c_ - a_) * w for u, w in GRID]
    pts = [q.lerp(c, 0.02) for q in pts]
    seen = False
    for d_ in dirs:
        if f.normal.dot(d_) > -0.25:                           # only viewpoints that see the face's back
            continue
        if any(ptree.ray_cast(q + d_ * 1e-4, d_, 3.0)[0] is None for q in pts):
            seen = True
            break
    if seen:
        poke.append(f)
bmesh.ops.delete(bm_p, geom=poke, context='FACES')
bmesh.ops.delete(bm_p, geom=[v for v in bm_p.verts if not v.link_faces], context='VERTS')
bm_p.to_mesh(mesh.data)
bm_p.free()
print('POKE-THROUGH faces removed', len(poke))
part = [d.value for d in mesh.data.attributes['part'].data]
region = [d.value for d in mesh.data.attributes['uv_region'].data]
head = [d.value for d in mesh.data.attributes['head'].data]
hid = [src_hid[kd.find(v.co)[1]] for v in mesh.data.vertices]
tex_set = [1 if pt == 1 else (2 if h == 1 else 0) for pt, h in zip(part, head)]
mesh.data.attributes.new('tex_set', 'INT', 'FACE').data.foreach_set('value', tex_set)
# body UVs re-taken per face from the full-detail body faces (POLYINTERP_NEAREST: each reduced face takes the corners of
# the nearest matching source face, interpolated): the texture-aware decimation slid jerkin corners across UV seams
# into the green shirt island (holes in the jerkin, user review 2026-10-14)
if BODY_UVS in ('installed', 'installed_col') and BODY_TRANSFER:
    # the installed full-detail mesh with its runtime UVs (work/source.blend 'Body' from import_source.py: merged
    # atlas UVs, body half u < 0.5) minus its head and cloak faces (cloak by the nearest rig_v3 face's part)
    with bpy.data.libraries.load(os.path.join(HERE, 'work', 'source.blend')) as (src2, dst2):
        dst2.objects = ['Body']
    body_src = dst2.objects[0]
    bpy.context.scene.collection.objects.link(body_src)
    for o in [o for o in bpy.data.objects if o.name.startswith('Rig') and o.type == 'ARMATURE']:
        bpy.data.objects.remove(o)
    for a in [a for a in bpy.data.actions if '.' in a.name]:
        bpy.data.actions.remove(a)
    body_src.modifiers.clear()
    body_src.parent = None
    sb = bmesh.new()
    sb.from_mesh(body_src.data)
    sb.faces.ensure_lookup_table()
    suv = sb.loops.layers.uv.active
    drop = []
    for f in sb.faces:
        u = sum(l[suv].uv.x for l in f.loops) / len(f.loops)
        _, _, near, _ = tree.find_nearest(f.calc_center_median())
        if u > 0.5 or labels['part'][near] == 1:
            drop.append(f)
    bmesh.ops.delete(sb, geom=drop, context='FACES')
    sb.to_mesh(body_src.data)
    sb.free()
    body_src.data.uv_layers.active = body_src.data.uv_layers[0]
    body_src.data.uv_layers[0].name = 'UVMap'
    # per face: the UV island of the nearest installed body face; per corner: the interpolated UV of its nearest point
    # on that island (no corner can cross a seam)
    sb = bmesh.new()
    sb.from_mesh(body_src.data)
    bmesh.ops.triangulate(sb, faces=sb.faces[:])
    sb.faces.ensure_lookup_table()
    sb.verts.ensure_lookup_table()
    suv = sb.loops.layers.uv.active
    key = lambda l: (round(l[suv].uv.x, 6), round(l[suv].uv.y, 6))
    island_of, islands = {}, []
    for f in sb.faces:                                     # islands: faces sharing an edge with equal UVs on both ends
        if f.index in island_of:
            continue
        stack = [f]; island_of[f.index] = len(islands); members = []
        while stack:
            g = stack.pop(); members.append(g)
            for l in g.loops:
                for o in l.edge.link_faces:
                    if o is g or o.index in island_of:
                        continue
                    ol = next(x for x in o.loops if x.edge == l.edge)
                    if {key(l), key(l.link_loop_next)} == {key(ol), key(ol.link_loop_next)}:
                        island_of[o.index] = len(islands); stack.append(o)
        islands.append(members)
    all_tree = BVHTree.FromBMesh(sb)
    island_trees = []
    for members in islands:
        verts = sorted({v.index for f in members for v in f.verts})
        vmap = {v: i for i, v in enumerate(verts)}
        island_trees.append((BVHTree.FromPolygons([sb.verts[v].co for v in verts],
                                                  [[vmap[v.index] for v in f.verts] for f in members]), members))

    def uv_at(face, point):
        a, b, c = (l.vert.co for l in face.loops)
        v0, v1, v2 = b - a, c - a, point - a
        d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
        den = d00 * d11 - d01 * d01 or 1e-12
        w1 = (d11 * d20 - d01 * d21) / den; w2 = (d00 * d21 - d01 * d20) / den; w0 = 1 - w1 - w2
        la, lb, lc = face.loops
        return (w0 * la[suv].uv.x + w1 * lb[suv].uv.x + w2 * lc[suv].uv.x,
                w0 * la[suv].uv.y + w1 * lb[suv].uv.y + w2 * lc[suv].uv.y)

    body_uv = {}                                          # (face index, corner) -> UV in the atlas
    for p in mesh.data.polygons:
        if tex_set[p.index] != 0:
            continue
        # the island of the outermost front-facing source surface along the face normal (the lower jerkin is two close
        # layers, jerkin skirt over shirt skirt: nearest-point lookups took the inner one), nearest point as fallback
        nrm_ = p.normal
        hit = None
        start, left = p.center + nrm_ * 0.03, 0.06
        for _ in range(4):
            loc_, hn_, hidx, dist_ = all_tree.ray_cast(start, -nrm_, left)
            if loc_ is None:
                break
            if hn_.dot(nrm_) > 0.0:
                hit = hidx
                break
            start, left = loc_ - nrm_ * 1e-5, left - dist_ - 1e-5
        if hit is None:
            hit = all_tree.find_nearest(p.center)[2]
        tree_i, members = island_trees[island_of[hit]]
        for k, vi in enumerate(p.vertices):
            loc, _, fi, _ = tree_i.find_nearest(mesh.data.vertices[vi].co)
            body_uv[(p.index, k)] = uv_at(members[fi], loc)
    sb.free()
    bpy.data.objects.remove(body_src)
bpy.data.objects.remove(source)
mesh.name = 'Thief'
mesh.data.name = 'Thief'

# --- materials (placeholders; export_tex.py assigns the texture sets) -------------------------------------------
mesh.data.materials.clear()
for name in ('Thief_A', 'ThiefCloak_A', 'ThiefHead_A'):
    mesh.data.materials.append(bpy.data.materials.new(name))
for p, t in zip(mesh.data.polygons, tex_set):
    p.material_index = t if t < 3 else 0

# --- UVs ------------------------------------------------------------------------------------------------------------
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(mesh.data)
bm.faces.ensure_lookup_table()
uv = bm.loops.layers.uv.active
# head: installed atlas UVs -> the head image (right half)
for f in bm.faces:
    if tex_set[f.index] == 2:
        for l in f.loops:
            u = (l[uv].uv.x * ATLAS_W - HALF - GUTTER) / HALF
            l[uv].uv = (u, l[uv].uv.y)
head_u = [l[uv].uv.x for f in bm.faces if tex_set[f.index] == 2 for l in f.loops]
if BODY_UVS in ('installed', 'installed_col'):   # body: the per-face transferred source UVs (installed body image)
    replaced = 0
    for f in bm.faces:
        if tex_set[f.index] == 0:
            use_transfer = False
            if BODY_TRANSFER and (f.index, 0) in body_uv:
                n_ = len(f.loops)
                cu = sum(l[uv].uv.x for l in f.loops) / n_ - sum(body_uv[(f.index, k)][0] for k in range(n_)) / n_
                cv = sum(l[uv].uv.y for l in f.loops) / n_ - sum(body_uv[(f.index, k)][1] for k in range(n_)) / n_
                use_transfer = (cu * cu + cv * cv) ** 0.5 > TRANSFER_TOL
                replaced += use_transfer
            for k, l in enumerate(f.loops):
                u_, v_ = body_uv[(f.index, k)] if use_transfer else (l[uv].uv.x, l[uv].uv.y)
                l[uv].uv = (u_ * ATLAS_W / HALF * (COL_FILL if BODY_UVS == 'installed_col' else 1.0), v_)
# seams along the source's uv_region borders and the texture-set borders
for e in bm.edges:
    faces = e.link_faces
    e.seam = len(faces) == 2 and (region[faces[0].index] != region[faces[1].index]
                                  or tex_set[faces[0].index] != tex_set[faces[1].index])
# body texel budget (user review of the first body retexture: the jerkin read soft): each island is scaled about its
# centre by its weight before packing; the detailed leather parts get more, the legs and the shirt hem less, and every
# island by its visibility (source `hid`, 1 = never seen), so hidden faces take almost nothing
PART_WEIGHT = {'Torso': 1.5, 'Pouch': 1.6, 'Strap': 1.5, 'Sheath': 1.5, 'Bracer': 1.4, 'Buckle': 1.5, 'Boot': 1.0,
               'Hand': 1.0, 'Legs': 0.75, 'Skirt': 0.7, 'Head': 1.0, 'Dagger': 0.3}
PART_NAMES = json.loads(bpy.context.scene['thf_parts'])


def islands_of(bm):
    """UV islands of the selected faces (faces joined across non-seam edges)."""
    faces = [f for f in bm.faces if f.select]
    seen, islands = set(), []
    for f in faces:
        if f.index in seen:
            continue
        stack, island = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop(); island.append(g)
            for l in g.loops:
                for o in l.edge.link_faces:
                    if o is g or o.index in seen or not o.select or l.edge.seam:
                        continue
                    seen.add(o.index); stack.append(o)
        islands.append(island)
    return islands


def uv_area(f, uvl):
    ls = f.loops
    return abs(sum(ls[i][uvl].uv.x * ls[(i + 1) % len(ls)][uvl].uv.y - ls[(i + 1) % len(ls)][uvl].uv.x * ls[i][uvl].uv.y
                   for i in range(len(ls)))) / 2


def collapsed_faces(bm):
    """Faces of islands the angle-based unwrap crushed (closed shells without a region border: boots, pouch, strap):
    UV area per 3D area under a third of the median island's."""
    uvl = bm.loops.layers.uv.active
    stats = []
    for island in islands_of(bm):
        a3 = sum(f.calc_area() for f in island)
        stats.append((island, sum(uv_area(f, uvl) for f in island) / max(a3, 1e-12)))
    ratios = sorted(r for _, r in stats)
    median = ratios[len(ratios) // 2]
    return [f.index for island, r in stats if r < median / 3 for f in island]


def weigh_islands(bm):
    """Scale every island about its centre to its target texel area: 3D area x part weight^2 x visibility."""
    uvl = bm.loops.layers.uv.active
    for island in islands_of(bm):
        verts = {v.index for f in island for v in f.verts}
        vis = 1.0 - sum(hid[i] for i in verts) / len(verts)
        names = [PART_NAMES[part[f.index]] for f in island]
        w = PART_WEIGHT.get(max(set(names), key=names.count), 1.0) * max(0.12, vis) ** 0.5
        if region_names[region[island[0].index]] == 'Hidden':
            w = 0.12
        a3 = sum(f.calc_area() for f in island)
        a2 = sum(uv_area(f, uvl) for f in island)
        if a2 < 1e-12:
            continue
        scale = w * (a3 / a2) ** 0.5
        cu = sum(l[uvl].uv.x for f in island for l in f.loops) / sum(len(f.loops) for f in island)
        cv = sum(l[uvl].uv.y for f in island for l in f.loops) / sum(len(f.loops) for f in island)
        for f in island:
            for l in f.loops:
                l[uvl].uv = (cu + (l[uvl].uv.x - cu) * scale, cv + (l[uvl].uv.y - cv) * scale)


region_names = json.loads(bpy.context.scene['thf_uv_regions'])
counts = {}
DAGGER = PART_NAMES.index('Dagger')
def cloak_uvs_from_upload(bm, uvl, path):
    """The cloak's UVs exactly as uploaded to Meshy (its texture was painted for them): each cloak triangle takes the
    corners of the upload triangle with the same centroid (glTF Y-up -> Blender Z-up)."""
    import struct
    import numpy as np
    from mathutils import kdtree as kdt
    raw = open(path, 'rb').read()
    n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + n]); binary = raw[28 + n:]

    def acc(i):
        a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
        c = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a['type']]
        dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a['componentType']]
        x = np.frombuffer(binary, dt, a['count'] * c, v.get('byteOffset', 0) + a.get('byteOffset', 0))
        return x.reshape(a['count'], c) if c > 1 else x
    tris = []
    for m in doc['meshes']:
        for pr in m['primitives']:
            P = acc(pr['attributes']['POSITION']); U = acc(pr['attributes']['TEXCOORD_0']); I = acc(pr['indices'])
            P = np.column_stack([P[:, 0], -P[:, 2], P[:, 1]])
            for t in I.reshape(-1, 3):
                tris.append((P[t], U[t]))
    tree = kdt.KDTree(len(tris))
    for i, (P, U) in enumerate(tris):
        tree.insert(P.mean(0), i)
    tree.balance()
    worst = 0.0
    for f in bm.faces:
        if not f.select:
            continue
        _, i, d = tree.find(f.calc_center_median())
        P, U = tris[i]
        worst = max(worst, d)
        for l in f.loops:
            k = int(np.argmin(((P - np.array(l.vert.co)) ** 2).sum(1)))
            l[uvl].uv = (float(U[k][0]), 1.0 - float(U[k][1]))        # glTF V flipped
    return worst


CLOAK_UPLOAD = os.path.join(HERE, 'work', 'thf_cloak_upload_v1.glb')      # the upload the cloak texture was made for
for wanted in ((1, 0) if BODY_UVS in ('new', 'baked') else (1,)):
    if wanted == 1 and os.path.exists(CLOAK_UPLOAD):
        for f in bm.faces:
            f.select = tex_set[f.index] == 1
        counts['cloak_match_mm'] = round(cloak_uvs_from_upload(bm, bm.loops.layers.uv.active, CLOAK_UPLOAD) * 1000, 3)
        bmesh.update_edit_mesh(mesh.data)
        counts[1] = sum(1 for f in bm.faces if f.select)
        continue
    for f in bm.faces:
        f.select = tex_set[f.index] == wanted and not (BODY_UVS == 'baked' and part[f.index] == DAGGER)
    bmesh.update_edit_mesh(mesh.data)
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, margin=0.003)
    if wanted == 0:
        bm = bmesh.from_edit_mesh(mesh.data)
        crushed = set(collapsed_faces(bm))
        if crushed:
            for f in bm.faces:
                f.select = f.index in crushed
            bmesh.update_edit_mesh(mesh.data)
            bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.003, area_weight=0.0, scale_to_bounds=False)
            bm = bmesh.from_edit_mesh(mesh.data)
            for f in bm.faces:
                f.select = tex_set[f.index] == 0 and not (BODY_UVS == 'baked' and part[f.index] == DAGGER)
        weigh_islands(bm)
        bmesh.update_edit_mesh(mesh.data)
        counts['crushed_body_faces'] = len(crushed)
    bpy.ops.uv.pack_islands(margin=0.003, rotate=True)
    bm = bmesh.from_edit_mesh(mesh.data)
    if wanted == 0:                          # keep a corner (new) or the dagger column (baked) free
        uvl = bm.loops.layers.uv.active
        fill = BODY_FILL if BODY_UVS == 'new' else DAGGER_COL[0] - 0.005
        for f in bm.faces:
            if f.select:
                for l in f.loops:
                    l[uvl].uv = (l[uvl].uv.x * fill, l[uvl].uv.y * fill)
        if BODY_UVS == 'baked':
            dagger_mesh.map_uvs(bm, uvl, DAGGER_COL, DAGGER_RECTS)
        bmesh.update_edit_mesh(mesh.data)
    counts[wanted] = sum(1 for f in bm.faces if f.select)
if BODY_UVS == 'installed_col':
    bm = bmesh.from_edit_mesh(mesh.data)
    dagger_mesh.map_uvs(bm, bm.loops.layers.uv.active, DAGGER_COL, DAGGER_RECTS)
    bmesh.update_edit_mesh(mesh.data)
if BODY_UVS == 'installed_col':
    # isolated wrong faces: a body face whose texture class (cloth mask at its UV centroid: shirt vs leather) differs
    # from all its edge neighbours slid across a chart border in the decimation (a green patch in the jerkin); its
    # corners take the UVs of the neighbouring faces at the same vertices
    import numpy as np
    mimg = bpy.data.images.load(os.path.join(HERE, 'work', 'thf_installed_mask_ext.png'))
    mw, mh = mimg.size
    marr = np.array(mimg.pixels[:], dtype=np.float32).reshape(mh, mw, mimg.channels)[..., 0]
    bm = bmesh.from_edit_mesh(mesh.data)
    bm.faces.ensure_lookup_table()
    uvl = bm.loops.layers.uv.active
    pl = bm.faces.layers.int['part']

    def cls(f):
        u = sum(l[uvl].uv.x for l in f.loops) / len(f.loops) / COL_FILL
        v = sum(l[uvl].uv.y for l in f.loops) / len(f.loops)
        return marr[min(max(int(v * mh), 0), mh - 1), min(max(int(u * mw), 0), mw - 1)] > 0.5
    body = [f for f in bm.faces if tex_set[f.index] == 0 and f[pl] != PART_NAMES.index('Dagger')]
    klass = {f.index: cls(f) for f in body}
    fixed = 0
    for f in body:
        nbrs = [o for e in f.edges for o in e.link_faces if o is not f and o.index in klass]
        if len(nbrs) < 2 or any(klass[o.index] == klass[f.index] for o in nbrs):
            continue
        for l in f.loops:
            other = next((ol for ol in l.vert.link_loops if ol.face in nbrs), None)
            if other is not None:
                l[uvl].uv = other[uvl].uv.copy()
        fixed += 1
    bmesh.update_edit_mesh(mesh.data)
    counts['isolated_faces_fixed'] = fixed
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'master_tex.blend'))

# --- Meshy uploads: one per new set, rest pose, no armature -------------------------------------------------------
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
for wanted, name in ((1, 'cloak'),) + (((0, 'body'),) if BODY_UVS == 'new' else ()):
    dup = mesh.copy()
    dup.data = mesh.data.copy()
    dup.modifiers.clear()
    dup.parent = None
    bpy.context.scene.collection.objects.link(dup)
    b2 = bmesh.new()
    b2.from_mesh(dup.data)
    b2.faces.ensure_lookup_table()
    if wanted == 1:
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if tex_set[f.index] != wanted], context='FACES')
    else:
        # the whole thief, so Meshy aligns the reference views to the same outline and occlusion as the references
        # (a body-only upload put the cloak's olive on the jerkin); cloak and head faces get tiny UVs in the free
        # top-right corner and their paint is not used
        uv2 = b2.loops.layers.uv.active
        for f in b2.faces:
            if tex_set[f.index] != 0:
                for l in f.loops:
                    l[uv2].uv = (DUMMY[0] + DUMMY[2] * l[uv2].uv.x, DUMMY[1] + DUMMY[2] * l[uv2].uv.y)
    b2.to_mesh(dup.data)
    b2.free()
    dup.data.materials.clear()
    for o in bpy.data.objects:
        o.select_set(o == dup)
    bpy.context.view_layer.objects.active = dup
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', f'thf_{name}_upload.glb'), use_selection=True,
                              export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                              export_materials='NONE', export_attributes=False)
    bpy.data.objects.remove(dup)
info = {'tris': sum(len(p.vertices) - 2 for p in mesh.data.polygons), 'crushed_body_faces': counts.get('crushed_body_faces'),
        'body_faces_transferred': globals().get('replaced'), 'isolated_faces_fixed': counts.get('isolated_faces_fixed'),
        'cloak_match_mm': counts.get('cloak_match_mm'),
        'body_uvs': BODY_UVS, 'dagger_col': DAGGER_COL, 'dagger_rects': DAGGER_RECTS, 'col_fill': COL_FILL,
        'faces_per_set': {'body': tex_set.count(0), 'cloak': tex_set.count(1), 'head': tex_set.count(2)},
        'head_u_range': [round(min(head_u), 4), round(max(head_u), 4)] if head_u else None,
        'actions': [a.name for a in bpy.data.actions]}
json.dump(info, open(os.path.join(HERE, 'work', 'master_tex.json'), 'w'), indent=1)
print('MASTER_TEX', json.dumps(info))
