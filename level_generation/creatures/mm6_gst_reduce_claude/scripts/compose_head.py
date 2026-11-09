"""1K head maps for the retextured reduced head (rules of ../mm6_gst_codex/scripts/compose_ghost.py, head set):
- base: skull faces Meshy head_retexture_r55 colour x rebaked native shade (work/head_shade.npy, .6 + .4 x shade), luminance
  quantile-matched per region (bone, cloth) to the installed head so it still sits with the body and the tier ramps;
  hood and brim faces the installed colour at the same 3D point and cloth side;
- bone region: the installed head mask at the same 3D point (installed geometry rasterised into its atlas head half);
- eyes: the square of the eye ellipsoids (add_eyes.py), constant palette colour; socket walls keep their texture;
- normal (convention measured), specular/roughness as compose_ghost; region mask R tabard (none), G bone, B eyes.
Writes textures/gst_head_{basecolor,normal,metal_rough}_1k.png, gst_head_region_mask.png, review/head_regions.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
P = Path(__file__).resolve().parents[1]; ROOT = P.parents[2]; N = 1024
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(ROOT / 'tools')); from normal_map_convention import measure  # noqa: E402
M = P / 'meshy/head_retexture_r55'; T = P / 'textures'


def raster(uv, pos):
    """per texel (rows top-down) the interpolated 3D position and coverage of UV triangles (uv: T x 3 x 2 in 0..1)"""
    cov = np.zeros((N, N), bool); out = np.zeros((N, N, 3), np.float32); tri = np.full((N, N), -1, np.int32)
    for i, (t, p) in enumerate(zip(uv * N, pos)):
        lo = np.maximum(0, np.floor(t.min(0)).astype(int)); hi = np.minimum(N - 1, np.ceil(t.max(0)).astype(int))
        m = np.column_stack([t[1] - t[0], t[2] - t[0]])
        if hi[0] < lo[0] or hi[1] < lo[1] or abs(np.linalg.det(m)) < 1e-12:
            continue
        xx, yy = np.meshgrid(np.arange(lo[0], hi[0] + 1) + .5, np.arange(lo[1], hi[1] + 1) + .5)
        w = (np.stack([xx, yy], -1) - t[0]) @ np.linalg.inv(m).T; w0 = 1 - w.sum(-1)
        inside = (w[..., 0] >= -.02) & (w[..., 1] >= -.02) & (w0 >= -.02)
        rows = N - 1 - (yy[inside] - .5).astype(int); cols = (xx[inside] - .5).astype(int)
        out[rows, cols] = w0[inside, None] * p[0] + w[inside, 0, None] * p[1] + w[inside, 1, None] * p[2]
        cov[rows, cols] = True; tri[rows, cols] = i
    return out, cov, tri


def pad(a, c):
    return a[tuple(ndimage.distance_transform_edt(~c, return_distances=False, return_indices=True))]


def save(a, p):
    Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5)).save(p, optimize=True)


def meshy(suffix):
    return np.asarray(Image.open(M / f'texture_urls_0_{suffix}.png').convert('RGB').resize((N, N), Image.LANCZOS), float) / 255


# new head surface
d = np.load(P / 'work/head_uv.npz'); pos, cov, tri = raster(d['uv'], d['pos'])
# installed head surface, mask and base colour (atlas head half)
src = np.load(P / 'work/mesh_in.npz'); w = src['wuv'].reshape(-1, 3, 2); head = w[:, :, 0].mean(1) > .5
wh = w[head].copy(); wh[..., 0] = (wh[..., 0] * 2080 - 1056) / 1024
opos, ocov, otri = raster(wh, src['verts'][src['faces'][head]])
omask = np.asarray(Image.open(P / 'work/region_mask.png').convert('RGBA'), float)[:, 1056:] / 255
obase = np.asarray(Image.open(P.parent / 'mm6_gst_codex/textures/gst_head_basecolor_1k.png').convert('RGB'), float) / 255
dist, near = cKDTree(opos[ocov]).query(pos[cov])
bones = np.zeros((N, N), bool); bones[cov] = omask[..., 1][ocov][near] > .5
obones = ocov & (omask[..., 1] > .5)
# eyes: the ellipsoids' square (add_eyes.py); the socket walls keep their own dark texture
blk = json.load(open(P / 'work/eye_block.json'))
eyes = np.zeros((N, N), bool)
eyes[int((1 - blk['uv_max'][1]) * N):int(np.ceil((1 - blk['uv_min'][1]) * N)),
     int(blk['uv_min'][0] * N):int(np.ceil(blk['uv_max'][0] * N))] = True
assert not (eyes & cov).any(), 'eye square overlaps head UVs'
cov = cov | eyes
bones &= ~eyes
cloth = np.zeros_like(cov)

a = meshy('base_color'); shade = .6 + .4 * np.load(P / 'work/head_shade.npy')
lin = R.srgb_to_linear(a) * shade[..., None]; a = np.where(lin <= .0031308, lin * 12.92, 1.055 * np.maximum(lin, 0) ** (1 / 2.4) - .055)
report = {'covered': int(cov.sum()), 'transfer_mm_p99': round(float(np.percentile(dist, 99)) * 1000, 2),
          'bone': int(bones.sum()), 'eyes': int(eyes.sum()),
          }
for name, new, old in [('bone', bones, obones), ('cloth', cov & ~bones & ~eyes, ocov & ~obones & ~(omask[..., 2] > .5))]:
    lum = R.luminance(a[new]); ref = R.luminance(obase[old])
    q = np.linspace(0, 1, 101); src_q = np.quantile(lum, q); ref_q = np.quantile(ref, q)
    gain = np.interp(lum, src_q, ref_q) / np.maximum(lum, 1e-4)
    a[new] = np.clip(a[new] * gain[:, None], 0, 1)
    report[f'{name}_lum_p10_50_90'] = [np.round(np.quantile(R.luminance(a[new]), [.1, .5, .9]), 3).tolist(),
                                       np.round(np.quantile(ref, [.1, .5, .9]), 3).tolist()]
# hood (and the tan brim piece at the hood opening, a bone-mask piece reaching y < -.1): the installed colour at the
# same 3D point, from installed texels on the same cloth layer (normals within 70 degrees; the hood is thin, and the
# nearest texel is often on its other side), inverse-distance over up to 12 neighbours. The new Meshy hood and brim
# had directional streaks; the installed hood matches the body cloth.
keys = np.round(d['pos'].reshape(-1, 3) * 1e5).astype(np.int64)
vid = np.unique(keys, axis=0, return_inverse=True)[1].reshape(-1, 3)
sk = np.where(d['skull'])[0]
from scipy.sparse import coo_matrix  # noqa: E402
from scipy.sparse.csgraph import connected_components  # noqa: E402
inc = coo_matrix((np.ones(3 * len(sk)), (np.repeat(np.arange(len(sk)), 3), vid[sk].reshape(-1)))).tocsr()
lab = connected_components(inc @ inc.T, directed=False)[1]
brim = np.zeros(len(d['skull']), bool)
for k in np.unique(lab):
    if d['pos'][sk[lab == k]][..., 1].min() < -.1:
        brim[sk[lab == k]] = True
skull_face = d['skull'] & ~brim
hood = cov & ~eyes & ~skull_face[np.maximum(tri, 0)]


def face_normals(p):
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]); return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


nn = face_normals(d['pos'])[tri[hood]]
on = face_normals(src['verts'][src['faces'][head]])[otri[ocov]]
kd = cKDTree(opos[ocov]); dist12, near12 = kd.query(pos[hood], k=12)
ok = np.einsum('nkc,nc->nk', on[near12], nn) > .34
wk = ok / np.maximum(dist12, 1e-5); none = wk.sum(1) == 0; wk[none, 0] = 1
a[hood] = (obase[ocov][near12] * wk[..., None]).sum(1) / wk.sum(1)[:, None]
report.update(hood_texels=int(hood.sum()), brim_faces=int(brim.sum()), hood_no_same_side=int(none.sum()),
              hood_transfer_mm_p99=round(float(np.percentile(np.where(ok, dist12, 1).min(1), 99)) * 1000, 2))
a[eyes] = .70

normal = meshy('normal'); score = measure(np.uint8(normal * 255 + .5)); assert abs(score) > .15, score
if score < 0:
    normal[..., 1] = 1 - normal[..., 1]
normal = normal * 2 - 1; normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-8); normal = (normal + 1) / 2
rough = meshy('roughness')[..., 0]; spec = np.full((N, N), .12); rough = np.clip(.90 + .12 * (rough - .5), .82, .97)
spec[bones] = .24; rough[bones] = .80; spec[eyes] = .38; rough[eyes] = .32
save(pad(a, cov), T / 'gst_head_basecolor_1k.png'); save(pad(normal, cov), T / 'gst_head_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rough, cov), np.zeros((N, N))], -1), T / 'gst_head_metal_rough_1k.png')
R.write_mask([ndimage.gaussian_filter(pad(m.astype(float), cov), .40) for m in (cloth, bones, eyes)],
             T / 'gst_head_region_mask.png', size=N)
overlay = a * .4
for m, color in zip((bones, eyes), ((.95, .55, .08), (.1, 1, .1))):
    overlay[m] = color
(P / 'review').mkdir(exist_ok=True); save(overlay, P / 'review/head_regions.png')
report['normal_correlation'] = score
(P / 'work/compose_head.json').write_text(json.dumps(report, indent=1)); print(json.dumps(report))
