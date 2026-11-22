"""Stage 1 (Blender): the high and low meshes of the Enchanted Boulder.

- Rock: the shipped MM8 great rock (boulder.json `rock`, LOD0 mesh), welded, turned by `rock_yaw_deg`, scaled to
  `rock_width` across (x) and `rock_height` high, sunk `sink` units below the origin (a skirt for slopes).
- Head: the MM6 mage's head (bearded; boulder.json `head`) in its rest pose, cut below the beard and behind
  `keep_depth` face lengths, holes filled, depth scaled by `relief` (bolder carving), leaned back by `face_tilt_deg`,
  scaled to `face_size` (chin to crown) and pushed into the rock's front so the nose tip stands `nose_out` in front
  of the rock surface there: half sunk.
- High: the union of both by voxel remesh (`voxel` units), then weathering in numpy: the joint between face and rock
  smoothed over `seam_band`, the face eroded (Laplacian passes), and two octaves of value noise displaced along the
  normals (the face gets less of the large octave, so brow, nose and mouth keep their shape). The underside is open.
- Low: the high collapse-decimated to `lod0_tris`, the face region kept denser.
Model units: Blender metres = game units / 100; front (the face) toward Blender -Y = glTF +Z; origin at the ground
under the rock's middle. Writes work/mesh.blend (High, Low; vertex group Face on both) and work/mesh.json.
Usage: blender -b --python build_mesh.py"""
import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..'))
cfg = json.load(open(os.path.join(HERE, 'boulder.json')))
work = os.path.join(PROJECT, 'work')
U = 0.01   # metres per game unit


def tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def import_mesh(path, rest=False):
    """One world-space mesh from a GLB: the LOD0 meshes (no _LOD suffix, no helper icospheres), joined."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, path))
    new = [o for o in bpy.data.objects if o not in before]
    if rest:
        for o in new:
            if o.type == 'ARMATURE':
                o.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for o in new:
        if o.type != 'MESH' or o.name.endswith(('_LOD1', '_LOD2', '_LOD3')) or o.name.startswith('Icosphere'):
            continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    return bm


def bm_object(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def verts_np(me):
    co = np.zeros(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get('co', co)
    return co.reshape(-1, 3)


def set_verts(me, co):
    me.vertices.foreach_set('co', co.astype(np.float32).ravel())
    me.update()


def smooth(me, lam, iterations, weight=None):
    """Laplacian passes over a mesh's vertices (numpy), weighted per vertex."""
    co = verts_np(me)
    ev = np.zeros(len(me.edges) * 2, np.int64)
    me.edges.foreach_get('vertices', ev)
    ev = ev.reshape(-1, 2)
    deg = np.maximum(np.bincount(ev.ravel(), minlength=len(co)), 1).astype(np.float64)
    w = np.ones(len(co)) if weight is None else weight
    for _ in range(iterations):
        acc = np.zeros_like(co)
        np.add.at(acc, ev[:, 0], co[ev[:, 1]])
        np.add.at(acc, ev[:, 1], co[ev[:, 0]])
        co = co + (lam * w)[:, None] * (acc / deg[:, None] - co)
    set_verts(me, co)


def voxel_remesh(ob, size):
    ob.data.remesh_voxel_size = size
    ob.data.remesh_voxel_adaptivity = 0.0
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.voxel_remesh()


# ------------------------------------------------------------------------------------------------------------- rock
bpy.ops.wm.read_factory_settings(use_empty=True)
rb = import_mesh(cfg['rock'])
bmesh.ops.rotate(rb, verts=rb.verts[:], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(cfg['rock_yaw_deg']), 3, 'Z'))
co = np.array([v.co for v in rb.verts])
lo, hi = co.min(0), co.max(0)
sx = cfg['rock_width'] * U / (hi[0] - lo[0])
sz = (cfg['rock_height'] + cfg['sink']) * U / (hi[2] - lo[2])
for v in rb.verts:
    v.co.x = (v.co.x - (lo[0] + hi[0]) / 2) * sx
    v.co.y = (v.co.y - (lo[1] + hi[1]) / 2) * sx
    v.co.z = (v.co.z - lo[2]) * sz - cfg['sink'] * U
# a flat underside for the union: cut 8 above the bottom and cap the cut with one planar face
cut = bmesh.ops.bisect_plane(rb, geom=rb.verts[:] + rb.edges[:] + rb.faces[:], dist=1e-6,
                             plane_co=(0, 0, (8 - cfg['sink']) * U), plane_no=(0, 0, 1), clear_inner=True)
bmesh.ops.holes_fill(rb, edges=[e for e in rb.edges if e.is_boundary], sides=0)
rock = bm_object(rb, 'Rock')
rb.free()
rco = verts_np(rock.data) / U
print('ROCK bounds', rco.min(0).round(1), rco.max(0).round(1), len(rock.data.polygons), 'faces')
rock_bvh = BVHTree.FromObject(rock, bpy.context.evaluated_depsgraph_get())


def nearest(bvh, points):
    """Distances (metres) from each point to a BVH's surface (1 m where nothing is found)."""
    out = np.empty(len(points))
    for k, p in enumerate(points):
        d = bvh.find_nearest(Vector(p))[3]
        out[k] = 1.0 if d is None else d
    return out


def rock_front(x, z):
    """The rock surface's y where a ray from the front (-Y) along +Y at (x, z) first hits it."""
    hit = rock_bvh.ray_cast(Vector((x, -10.0, z)), Vector((0, 1, 0)))
    return hit[0].y if hit[0] is not None else None


# ------------------------------------------------------------------------------------------------------------- head
hb = import_mesh(cfg['head'], rest=True)
co = np.array([v.co for v in hb.verts])
top = co[:, 2].max()
height = top - co[:, 2].min()
head = co[:, 2] > top - 0.16 * height
front = co[head, 1].min()
centre = head & (np.abs(co[:, 0]) < 0.014 * height) & (co[:, 1] < front + 0.035 * height)
# the chin under a beard: the face's lowest front-centre point above the beard's tip is hard to find, so the chin
# is taken at the mouth's height minus a fixed share of the face (nose tip - 0.45 face lengths)
nose_i = np.argmin(np.where(head & (np.abs(co[:, 0]) < 0.01 * height), co[:, 1], 1e9))
nose = co[nose_i]
chin = nose[2] - 0.55 * (top - nose[2])
face_len = top - chin
print('HEAD source height %.3f top %.3f nose z %.3f y %.3f chin %.3f' % (height, top, nose[2], nose[1], chin))
cut_z = chin - cfg['beard_below_chin'] * face_len
bmesh.ops.delete(hb, geom=[v for v in hb.verts if v.co.z < cut_z], context='VERTS')
s = cfg['face_size'] * U / face_len
tilt = Matrix.Rotation(math.radians(-cfg['face_tilt_deg']), 3, 'X')   # top leans back (+Y)
for v in hb.verts:
    p = Vector(((v.co.x - nose[0]) * s, (v.co.y - nose[1]) * s * cfg['relief'], (v.co.z - chin) * s))
    v.co = tilt @ p
# place: chin at face_z, nose tip nose_out in front of the rock surface at the nose's height
nose_local = tilt @ Vector((0, 0, (nose[2] - chin) * s))
zx = cfg['face_x'] * U
z_nose = cfg['face_z'] * U + nose_local.z
yr = rock_front(zx, z_nose)
shift = Vector((zx, yr - cfg['nose_out'] * U - nose_local.y, cfg['face_z'] * U))
for v in hb.verts:
    v.co += shift
src = bm_object(hb, 'HeadSource')
hb.free()
src_bvh = BVHTree.FromObject(src, bpy.context.evaluated_depsgraph_get())

# The carving is a relief: the head's front surface as a height field over the front view (x, z), read by rays along
# +Y every `relief_step` units. Inside the mask ellipse (from `sink_from`) it sinks smoothly back to `back` units inside
# the rock surface at `cut` (no ledge where it meets the rock); outside it lies there. A Gaussian blur of `blur` units
# weathers it (beard strands, eyelids and lips soften; brow, nose, mouth and beard mass stay).
mk = cfg['mask']
FL = cfg['face_size']                       # face length in units
zc_u = cfg['face_z'] + mk['zc'] * FL
rx_u, rz_u = mk['rx'] * FL, mk['rz'] * FL
step = cfg['relief_step']
xs = np.arange(zx / U - rx_u * mk['cut'] - 4 * step, zx / U + rx_u * mk['cut'] + 4 * step + 1e-6, step)
zs = np.arange(zc_u - rz_u * mk['cut'] - 4 * step, zc_u + rz_u * mk['cut'] + 4 * step + 1e-6, step)
X, Z = np.meshgrid(xs, zs)
Y = np.full(X.shape, np.nan)
R = np.full(X.shape, np.nan)            # the rock's front surface
for i in range(X.shape[0]):
    for j in range(X.shape[1]):
        hit = src_bvh.ray_cast(Vector((X[i, j] * U, -10.0, Z[i, j] * U)), Vector((0, 1, 0)))
        if hit[0] is not None:
            Y[i, j] = hit[0].y / U
        r = rock_front(X[i, j] * U, Z[i, j] * U)
        if r is not None:
            R[i, j] = r / U
Rhit = R.copy()
print('RELIEF rock misses inside the mask: %d' % int((np.isnan(R) & (np.sqrt(((X - zx / U) / rx_u) ** 2
                                                                          + ((Z - zc_u) / rz_u) ** 2) < mk['cut'])).sum()))
R = np.where(np.isnan(R), np.nanmax(R), R)
back = R + cfg['back']
Y = np.where(np.isnan(Y), back, np.minimum(Y, back))
E = np.sqrt(((X - zx / U) / rx_u) ** 2 + ((Z - zc_u) / rz_u) ** 2)
t = np.clip((E - mk['sink_from']) / (mk['cut'] - mk['sink_from']), 0, 1)
Y = Y + t * t * (3 - 2 * t) * np.maximum(back - Y, 0)
Y = np.where(E >= mk['cut'], back, np.minimum(Y, back))


def blur(img, sigma):
    r = int(3 * sigma) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    pad = np.pad(img, r, mode='edge')
    tmp = np.apply_along_axis(lambda m: np.convolve(m, k, mode='valid'), 1, pad)
    return np.apply_along_axis(lambda m: np.convolve(m, k, mode='valid'), 0, tmp)


Y = blur(Y, cfg['blur'] / step)
# the slab: front = the relief, back = the rock surface + `back` + 20 (inside the rock), sides closing the rim; only
# the grid cells inside the mask ellipse (plus two cells), so nothing of it can stand outside the rock
ny, nx = X.shape
inside = (E < mk['cut'] + 2 * step / min(rx_u, rz_u)) & np.isfinite(Rhit)
cells = inside[:-1, :-1] & inside[1:, :-1] & inside[:-1, 1:] & inside[1:, 1:]
bm = bmesh.new()
fv, bv = {}, {}


def vert_pair(i, j):
    if (i, j) not in fv:
        fv[i, j] = bm.verts.new((X[i, j] * U, Y[i, j] * U, Z[i, j] * U))
        bv[i, j] = bm.verts.new((X[i, j] * U, (back[i, j] + 20) * U, Z[i, j] * U))
    return fv[i, j], bv[i, j]


edge_count = {}
for i in range(ny - 1):
    for j in range(nx - 1):
        if not cells[i, j]:
            continue
        loop = [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]
        pairs = [vert_pair(*c) for c in loop]
        bm.faces.new([p[0] for p in pairs])
        bm.faces.new([p[1] for p in reversed(pairs)])
        for k in range(4):
            e = (loop[k], loop[(k + 1) % 4])
            key = tuple(sorted(e))
            edge_count[key] = edge_count.get(key, []) + [e]
for key, uses in edge_count.items():
    if len(uses) == 1:                      # a rim edge: close it with a side quad
        (a0, a1) = uses[0]
        bm.faces.new((fv[a1], fv[a0], bv[a0], bv[a1]))
bm.normal_update()
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
head_ob = bm_object(bm, 'Head')
bm.free()
head_bvh = BVHTree.FromObject(head_ob, bpy.context.evaluated_depsgraph_get())
src.hide_render = True
print('FACE scale %.1f units per source unit, chin z %.1f, nose at y %.1f (rock front %.1f), relief grid %d x %d'
      % (s / U, cfg['face_z'], (yr - cfg['nose_out'] * U) / U, yr / U, nx, ny))

# ------------------------------------------------------------------------------------------------------------- union
union = bpy.data.objects.new('High', bpy.data.meshes.new('High'))
bpy.context.scene.collection.objects.link(union)
bm = bmesh.new()
bm.from_mesh(rock.data)
bm.from_mesh(head_ob.data)
bm.to_mesh(union.data)
bm.free()
voxel_remesh(union, cfg['voxel'] * U)
me = union.data
print('HIGH voxel remesh', len(me.polygons), 'quads')
if cfg.get('debug_raw'):
    raw = bpy.data.objects.new('HighRaw', me.copy())
    bpy.context.scene.collection.objects.link(raw)

# per-vertex distances to the two sources
co = verts_np(me)
d_rock = nearest(rock_bvh, co) / U
d_head = nearest(head_bvh, co) / U
is_face = (d_head < d_rock) & (d_head < 3 * cfg['voxel'])
band = cfg['seam_band']
seam_w = np.clip(1.0 - np.maximum(d_rock, d_head) / band, 0, 1) ** 0.7
face_w = is_face.astype(float)

# neighbours (edges) for Laplacian passes
ev = np.zeros(len(me.edges) * 2, np.int64)
me.edges.foreach_get('vertices', ev)
ev = ev.reshape(-1, 2)
deg = np.bincount(ev.ravel(), minlength=len(co)).astype(np.float64)


def laplace(co, weight, lam, iterations):
    for _ in range(iterations):
        acc = np.zeros_like(co)
        np.add.at(acc, ev[:, 0], co[ev[:, 1]])
        np.add.at(acc, ev[:, 1], co[ev[:, 0]])
        mean = acc / np.maximum(deg, 1)[:, None]
        co = co + (lam * weight)[:, None] * (mean - co)
    return co


co = laplace(co, seam_w, 0.6, 14)                                   # the joint grows into the rock
co = laplace(co, face_w, 0.5, cfg['face_erode_iterations'])        # weathered features (shrinks a little)
co = laplace(co, np.ones(len(co)), 0.25, 1)                         # voxel steps
set_verts(me, co)
if cfg.get('debug_raw'):
    dbg = bpy.data.objects.new('HighLap', me.copy())
    bpy.context.scene.collection.objects.link(dbg)


def noise3(P, period, seed):
    """Smooth 3D value noise in [-1, 1] (trilinear on a hashed lattice with smoothstep), period in units."""
    q = P / period
    i = np.floor(q).astype(np.int64)
    f = q - i
    f = f * f * (3 - 2 * f)
    rng = np.random.default_rng(seed)
    table = rng.random(4096)
    perm = rng.permutation(4096)

    def h(a, b, c):
        return table[perm[(perm[(perm[a % 4096] + b) % 4096] + c) % 4096]]
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + w * h(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz)
    return out * 2 - 1


# vertex normals (area-weighted face normals, numpy; the remesh's quads)
fv = np.zeros(len(me.polygons) * 4, np.int64)
me.polygons.foreach_get('vertices', fv)
fv = fv.reshape(-1, 4)
fn = np.cross(co[fv[:, 2]] - co[fv[:, 0]], co[fv[:, 3]] - co[fv[:, 1]])
nrm = np.zeros_like(co)
for k in range(4):
    np.add.at(nrm, fv[:, k], fn)
nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
P = co / U
(pb, ab), (ps, as_) = cfg['noise']['big'], cfg['noise']['small']
big = noise3(P, pb, 11) + 0.5 * noise3(P, pb / 2.1, 12)
small = noise3(P, ps, 13) + 0.5 * noise3(P, ps / 2.3, 14)
fb, fs = cfg['face_noise']                                             # the face keeps its forms: less noise
disp = ab * big * np.where(is_face, fb, 1.0) + as_ * small * np.where(is_face, fs, 1.0)
disp *= np.clip((P[:, 2] + cfg['sink']) / 12.0, 0, 1)               # the skirt's rim stays where it is
co = co + nrm * (disp * U)[:, None]
set_verts(me, co)
if cfg.get('debug_raw'):
    sel = (np.abs(P[:, 0]) < 60) & (P[:, 2] > 60) & (P[:, 2] < 200) & (P[:, 1] < -120)
    nb = np.einsum('ij,ij->i', nrm[ev[:, 0]], nrm[ev[:, 1]])
    def rough(c):
        acc = np.zeros_like(c)
        np.add.at(acc, ev[:, 0], c[ev[:, 1]])
        np.add.at(acc, ev[:, 1], c[ev[:, 0]])
        return np.percentile(np.linalg.norm(acc / np.maximum(deg, 1)[:, None] - c, axis=1)[sel] / U, [50, 99])
    print('DBG rough before', rough(co - nrm * (disp * U)[:, None]), 'after', rough(co),
          'disp-only', rough(nrm * (disp * U)[:, None] + 0 * co), 'nrm', rough(nrm * U))
    print('DBG face share %.3f disp p1/p99 %s big %s small %s normal-dot p1 %.3f' % (
        is_face[sel].mean(), np.percentile(disp[sel], [1, 99]).round(2), np.percentile(big[sel], [1, 99]).round(2),
        np.percentile(small[sel], [1, 99]).round(2), np.percentile(nb, 1)))

# open underside: faces at the skirt's bottom facing down
bm = bmesh.new()
bm.from_mesh(me)
bm.normal_update()
z0 = -cfg['sink'] * U
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=(0, 0, z0 + 11 * U),
                       plane_no=(0, 0, 1), clear_inner=True)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.to_mesh(me)
bm.free()
me.shade_smooth()
co = verts_np(me)
d_head = nearest(head_bvh, co) / U
d_rock = nearest(rock_bvh, co) / U
face_sel = np.nonzero((d_head < d_rock) & (d_head < 6))[0]
g = union.vertex_groups.new(name='Face')
g.add([int(i) for i in face_sel], 1.0, 'REPLACE')
print('HIGH triangles', tris(me), 'face verts', len(face_sel))

# ------------------------------------------------------------------------------------------------------------- low
low = bpy.data.objects.new('Low', me.copy())
bpy.context.scene.collection.objects.link(low)
mod = low.modifiers.new('dec', 'DECIMATE')
mod.decimate_type = 'COLLAPSE'
mod.use_collapse_triangulate = True
# face kept denser: Blender's collapse cost grows by 1 + (2 - w1 - w2) * factor (a weight of 0 locks a vertex), so
# the rock gets weight 1 and the face `face_weight`
dec = low.vertex_groups.new(name='Dec')
dec.add([int(i) for i in np.setdiff1d(np.arange(len(me.vertices)), face_sel)], 1.0, 'REPLACE')
dec.add([int(i) for i in face_sel], cfg['face_weight'], 'REPLACE')
mod.vertex_group = 'Dec'
mod.vertex_group_factor = 1.0
full = tris(me)
ratio = cfg['lod0_tris'] / full
for _ in range(6):    # the vertex group skews the count: adjust the ratio until LOD0 lands near its budget
    mod.ratio = ratio
    dg = bpy.context.evaluated_depsgraph_get()
    n = len(low.evaluated_get(dg).data.polygons)
    if abs(n - cfg['lod0_tris']) < 0.03 * cfg['lod0_tris']:
        break
    ratio *= cfg['lod0_tris'] / n
dg = bpy.context.evaluated_depsgraph_get()
lme = bpy.data.meshes.new_from_object(low.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
low.modifiers.clear()
old = low.data
low.data = lme
bpy.data.meshes.remove(old)
bm = bmesh.new()
bm.from_mesh(lme)
bmesh.ops.dissolve_degenerate(bm, dist=2e-4, edges=bm.edges[:])
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='BEAUTY')
bm.to_mesh(lme)
bm.free()
lme.name = 'Low'
lme.shade_smooth()
lco = verts_np(lme)
ld_head = nearest(head_bvh, lco) / U
ld_rock = nearest(rock_bvh, lco) / U
low.vertex_groups.clear()
lg = low.vertex_groups.new(name='Face')
lg.add([int(i) for i in np.nonzero((ld_head < ld_rock) & (ld_head < 8))[0]], 1.0, 'REPLACE')
face_tris = sum(1 for p in lme.polygons if all(lg.index in [g.group for g in lme.vertices[v].groups]
                                                  for v in p.vertices))
lo, hi = lco.min(0) / U, lco.max(0) / U
print('LOW triangles', tris(lme), 'face triangles', face_tris)
print('BOUNDS units', tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi))
for o in (rock, head_ob):
    o.hide_render = True
    o.hide_set(True)
json.dump({'bounds_units': [lo.tolist(), hi.tolist()], 'high_tris': tris(me), 'low_tris': tris(lme),
           'low_face_tris': face_tris}, open(os.path.join(work, 'mesh.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'mesh.blend'))
print('MESH_DONE')
