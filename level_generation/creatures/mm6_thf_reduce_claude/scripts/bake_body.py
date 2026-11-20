"""Bake the installed body maps onto the reduced body's fresh layout (BODY_UVS = 'baked' in build_master_tex.py).

For every texel of a reduced body triangle (2K, daggers excluded): its rest position and interpolated normal; the
first front-facing installed surface hit by a ray cast inward along that normal from 30 mm outside (nearest point if none) on the
installed full-detail surface (work/source.blend 'Body' minus cloak faces and the never-seen 'Hidden' inner layers,
both by the nearest rig_v3 face); hits in the atlas head half (the installed head set also holds the jerkin front)
sample the head-set crops (textures/thf_head_*), the rest the installed body maps; the installed atlas UV there (body image = atlas body half) samples
the installed base colour, metallic-roughness and the extended cloth mask (work/thf_installed_mask_ext.png); the normal
map is carried through object space (source tangent frame -> target tangent frame, per triangle, with interpolated
normals). Writes work/bake_body.npz (base, mr, normal, mask, covered; 2K float)."""
import json
import os

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRE = os.path.dirname(HERE)
OLD = os.path.join(CRE, 'mm6_thf_claude', 'textures')
SIZE = 2048
ATLAS_W, HALF = 2080, 1024

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master_tex.blend'))
mesh = bpy.data.objects['Thief']
rig = bpy.data.objects['Thief_Rig']
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
with bpy.data.libraries.load(os.path.join(HERE, 'work', 'source.blend')) as (src, dst):
    dst.objects = ['Body']
body = dst.objects[0]


def image(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, img.channels)[::-1]     # row 0 = top
    return a


base_img = image(os.path.join(OLD, 'thf_a_basecolor_1k.png'))[..., :3]
if os.environ.get('BAKE_DEBUG'):                       # a fine coloured checker in installed UV space: mapping check
    yy, xx = np.mgrid[0:1024, 0:1024]
    cell = (xx // 12 + yy // 12) % 2
    base_img = np.stack([(xx / 1024) * (0.5 + 0.5 * cell), (yy / 1024) * (0.5 + 0.5 * cell), 0.3 + 0.4 * cell], -1).astype(np.float32)
mr_img = image(os.path.join(OLD, 'thf_metal_rough_1k.png'))[..., :3]
nrm_img = image(os.path.join(OLD, 'thf_normal_1k.png'))[..., :3]
mask_img = image(os.path.join(HERE, 'work', 'thf_installed_mask_ext.png'))[..., 0]
# the installed head set (atlas right half) also carries the jerkin front and the neck (TorsoF faces): its maps too
T_HEAD = os.path.join(HERE, 'textures')
head_imgs = {'base': image(os.path.join(T_HEAD, 'thf_head_basecolor_1k.png'))[..., :3],
             'mr': image(os.path.join(T_HEAD, 'thf_head_metal_rough_1k.png'))[..., :3],
             'normal': image(os.path.join(T_HEAD, 'thf_head_normal_1k.png'))[..., :3],
             'mask': image(os.path.join(T_HEAD, 'thf_head_region_mask.png'))[..., 0]}


def sample(img, u, v):
    """Bilinear lookup at body-image UVs (glTF V down = image row from the top)."""
    h, w = img.shape[:2]
    x = np.clip(u * w - 0.5, 0, w - 1.001)
    y = np.clip((1 - v) * h - 0.5, 0, h - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    if img.ndim == 3:
        fx, fy = fx[:, None], fy[:, None]
    return ((img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx) * (1 - fy)
            + (img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx) * fy)


def tris_of(me, keep):
    """Loop triangles of the faces where keep(poly index): vertex positions, corner normals, corner UVs."""
    me.calc_loop_triangles()
    uvd = me.uv_layers.active.data
    cn = me.corner_normals
    P, N, U, F = [], [], [], []
    for t in me.loop_triangles:
        if not keep(t.polygon_index):
            continue
        P.append([me.vertices[v].co[:] for v in t.vertices])
        N.append([cn[l].vector[:] for l in t.loops])
        U.append([uvd[l].uv[:] for l in t.loops])
        F.append(t.polygon_index)
    return np.array(P), np.array(N), np.array(U), F


# --- source: installed body surface ---------------------------------------------------------------------------------
src_part_tree = None
rig3 = os.path.join(CRE, 'mm6_thf_claude', 'work', 'rig_v3.blend')
with bpy.data.libraries.load(rig3) as (src3, dst3):
    dst3.objects = ['Thief']
ref = dst3.objects[0]
ref_part = [d.value for d in ref.data.attributes['part'].data]
ref_region = [d.value for d in ref.data.attributes['uv_region'].data]
hidden = json.loads(bpy.context.scene['thf_uv_regions']).index('Hidden')
ref.data.calc_loop_triangles()
ref_tree = BVHTree.FromPolygons([v.co for v in ref.data.vertices], [p.vertices[:] for p in ref.data.polygons])
cloak = json.loads(bpy.context.scene['thf_parts']).index('Cloak')
buv = body.data.uv_layers.active.data


def body_face_ok(pi):
    p = body.data.polygons[pi]
    _, _, near, _ = ref_tree.find_nearest(p.center)
    return ref_part[near] != cloak and ref_region[near] != hidden      # never-seen inner layers: no paint to take


SP, SN, SU, SF = tris_of(body.data, body_face_ok)
IN_HEAD = SU[:, :, 0].mean(1) > 0.5                          # triangle in the atlas head half
SU = np.where(IN_HEAD[:, None, None], np.stack([(SU[..., 0] * ATLAS_W - HALF - 32) / HALF, SU[..., 1]], -1),
              np.stack([SU[..., 0] * ATLAS_W / HALF, SU[..., 1]], -1))      # atlas -> its own image
src_tree = BVHTree.FromPolygons([Vector(p) for tri in SP for p in tri], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(SP))])


def frames(P, U):
    """Per-triangle tangent (along +u) and bitangent (along +v) in object space."""
    e1, e2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
    d1, d2 = U[:, 1] - U[:, 0], U[:, 2] - U[:, 0]
    r = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    r = np.where(np.abs(r) < 1e-12, 1e-12, r)
    T = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / r[:, None]
    B = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / r[:, None]
    return T, B


ST, SB = frames(SP, SU)

# --- target: reduced body triangles in their new UVs ----------------------------------------------------------------
tex_set = [d.value for d in mesh.data.attributes['tex_set'].data]
piece = [d.value for d in mesh.data.attributes['dagger_piece'].data] if 'dagger_piece' in mesh.data.attributes else None
TP, TN, TU, TF = tris_of(mesh.data, lambda i: tex_set[i] == 0 and not (piece and piece[i]))
TT, TB = frames(TP, TU)

pos, nrm, tri_id, px = [], [], [], []
for i in range(len(TP)):
    uv = TU[i] * SIZE
    uv = np.column_stack([uv[:, 0], SIZE - uv[:, 1]])
    x0, y0 = np.floor(uv.min(0)).astype(int)
    x1, y1 = np.ceil(uv.max(0)).astype(int)
    ys, xs = np.mgrid[max(y0, 0):min(y1 + 1, SIZE), max(x0, 0):min(x1 + 1, SIZE)]
    p = np.stack([xs + 0.5, ys + 0.5], -1).reshape(-1, 2)
    a, b, c = uv
    m = np.array([b - a, c - a]).T
    if abs(np.linalg.det(m)) < 1e-9:
        continue
    l12 = np.linalg.solve(m, (p - a).T).T
    l0 = 1 - l12[:, 0] - l12[:, 1]
    w = np.column_stack([l0, l12])
    inside = (w >= -0.02).all(1)                                   # a little dilation closes cracks between triangles
    if not inside.any():
        continue
    w = np.clip(w[inside], 0, None); w /= w.sum(1, keepdims=True)
    pos.append(w @ TP[i]); nrm.append(w @ TN[i]); tri_id.append(np.full(len(w), i)); px.append(p[inside].astype(int))
pos, nrm, tri_id, px = np.concatenate(pos), np.concatenate(nrm), np.concatenate(tri_id), np.concatenate(px)
print('TEXELS', len(pos))

hit_tri = np.zeros(len(pos), int)
hit_loc = np.zeros((len(pos), 3))
# the outermost source surface along the target normal (the installed model has the shirt just beneath the jerkin
# skirt, and plain nearest-point lookups landed on it: green patches); nearest point only where no ray hits
nunit = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
OUT, REACH = 0.03, 0.06
fallback = 0
for k in range(len(pos)):
    n = Vector(nunit[k]); p = Vector(pos[k])
    start, left, loc = p + n * OUT, REACH, None
    for _ in range(4):                                     # the first front-facing surface along the ray
        hit, hn, hidx, dist = src_tree.ray_cast(start, -n, left)
        if hit is None:
            break
        if hn.dot(n) > 0.0:
            loc, idx = hit, hidx
            break
        start, left = hit - n * 1e-5, left - dist - 1e-5
    if loc is None:
        loc, _, idx, _ = src_tree.find_nearest(p)
        fallback += 1
    hit_tri[k] = idx
    hit_loc[k] = loc
print('RAYS fallback to nearest', fallback, 'of', len(pos))
# barycentric of the hit in the source triangle
A, Bv, C = SP[hit_tri, 0], SP[hit_tri, 1], SP[hit_tri, 2]
v0, v1, v2 = Bv - A, C - A, hit_loc - A
d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
den = np.where(np.abs(d00 * d11 - d01 * d01) < 1e-18, 1e-18, d00 * d11 - d01 * d01)
w1 = (d11 * d20 - d01 * d21) / den
w2 = (d00 * d21 - d01 * d20) / den
W = np.column_stack([1 - w1 - w2, w1, w2])
suv = (W[:, :, None] * SU[hit_tri]).sum(1)
sn = (W[:, :, None] * SN[hit_tri]).sum(1)
hh = IN_HEAD[hit_tri]


def both(body_img, head_img):
    out = sample(body_img, suv[:, 0], suv[:, 1])
    if hh.any():
        out[hh] = sample(head_img, suv[hh, 0], suv[hh, 1])
    return out


base = both(base_img, head_imgs['base'])
mr = both(mr_img, head_imgs['mr'])
mask = both(mask_img, head_imgs['mask'])
tn = both(nrm_img, head_imgs['normal']) * 2 - 1
print('HEAD-SET hits', int(hh.sum()), 'of', len(hh))
if os.environ.get('BAKE_STATS'):
    import collections
    regions = json.loads(bpy.context.scene['thf_uv_regions'])
    t_reg = [d.value for d in mesh.data.attributes['uv_region'].data]
    src_reg = []
    for fi in SF:
        _, _, near, _ = ref_tree.find_nearest(body.data.polygons[fi].center)
        src_reg.append(regions[ref_region[near]])
    stats = collections.defaultdict(collections.Counter)
    for k in range(0, len(pos), 7):
        stats[regions[t_reg[TF[tri_id[k]]]]][src_reg[hit_tri[k]]] += 1
    for r, c in sorted(stats.items()):
        print('STAT', r, c.most_common(4))
    # sampling scale: source pixels moved per target texel step (1K source, 2K target)
    key = {(int(x), int(y)): k for k, (x, y) in enumerate(px)}
    scale = collections.defaultdict(list)
    for k in range(0, len(px), 13):
        j = key.get((int(px[k][0]) + 1, int(px[k][1])))
        if j is None or tri_id[j] != tri_id[k]:
            continue
        d = np.abs(suv[j] - suv[k]) * 1024
        scale[regions[t_reg[TF[tri_id[k]]]]].append(float(np.hypot(*d)))
    for r, v in sorted(scale.items()):
        print('SCALE', r, 'median src px per target px %.3f' % np.median(v), 'p90 %.3f' % np.percentile(v, 90))


def basis(T, B, N):
    N = N / np.linalg.norm(N, axis=1, keepdims=True)
    T = T - N * (T * N).sum(1, keepdims=True); T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
    B = B - N * (B * N).sum(1, keepdims=True) - T * (B * T).sum(1, keepdims=True)
    B /= np.maximum(np.linalg.norm(B, axis=1, keepdims=True), 1e-12)
    return T, B, N


sT, sB, sN = basis(ST[hit_tri], SB[hit_tri], sn)
obj = tn[:, 0:1] * sT + tn[:, 1:2] * sB + tn[:, 2:3] * sN
tT, tB, tN = basis(TT[tri_id], TB[tri_id], nrm)
enc = np.column_stack([(obj * tT).sum(1), (obj * tB).sum(1), (obj * tN).sum(1)])
enc /= np.maximum(np.linalg.norm(enc, axis=1, keepdims=True), 1e-12)

out = {k: np.zeros((SIZE, SIZE, c), np.float32) for k, c in (('base', 3), ('mr', 3), ('normal', 3), ('mask', 1))}
covered = np.zeros((SIZE, SIZE), bool)
ix, iy = px[:, 0], px[:, 1]
out['base'][iy, ix] = base
out['mr'][iy, ix] = mr
out['normal'][iy, ix] = enc * 0.5 + 0.5
out['mask'][iy, ix, 0] = mask
covered[iy, ix] = True
np.savez_compressed(os.path.join(HERE, 'work', 'bake_body.npz'), covered=covered, **out)
dist = np.linalg.norm(hit_loc - pos, axis=1)
print('BAKED texels', int(covered.sum()), 'hit distance mean %.2f mm p99 %.2f mm' % (dist.mean() * 1000, np.percentile(dist, 99) * 1000))
