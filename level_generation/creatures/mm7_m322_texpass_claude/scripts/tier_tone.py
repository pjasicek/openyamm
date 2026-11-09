"""Engine colour per tier (region ramps applied as viewer_variants.bake), installed against the pass, at the same
surface points of the texture-pass layout, plus the face seam measurements the user asked for.

Per tier: area-weighted mean sRGB of trousers and hair (texels both masks call that region) and of skin zones:
forehead, left/right cheek, chin, neck above and below the head-set boundary (the head paint's crossfade starts at
the boundary), upper chest, upper arms; the largest pairwise skin-zone difference (max channel); the head/body step
across the neck crossfade (2 cm bands either side of the boundary); and the chart-seam step on face and neck skin
(mean / p95 max-channel difference of the two sides of every chart seam vertex, 20 % in from the corner, where
both sides are skin-coloured in both maps).
Usage: tier_tone.py <installed glb> <pass maps prefix | pass glb> [out json]"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402
from viewer_variants import bake  # noqa: E402
import texlib  # noqa: E402
import seam_level  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import texture_quality as TQ  # noqa: E402

before_path, after = sys.argv[1], sys.argv[2]
S = 2048
L = np.load(HERE / 'work' / 'uv_fine.npz')
d = np.load(HERE / 'work' / 'lod0_before.npz')
r = np.load(HERE / 'work' / 'approved_fine_raster2048.npz')
tid, bary = r['tri_id'], r['bary']
cov = tid >= 0
t = np.where(cov, tid, 0)
uv, xyz = L['uv'], L['xyz']
tri, weld, hf, piece = d['tri'], d['weld'], d['head_face'], d['piece']
wtri = weld[tri]
point = (xyz[t] * bary[..., None]).sum(-2)
a3 = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
a2 = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1]) - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
w = np.where(cov, (a3 / np.maximum(a2, 1e-12))[t], 0)
fn = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
nz, nx = fn[t, 2], fn[t, 0]
x, y = point[..., 0], point[..., 1]
tp = piece[t]

gb = Glb(before_path)
old_base = gb.image(0).convert('RGB')
old_mask = gb.image(3)
old_uv = d['uv'][tri]
if after.endswith('.glb'):
    ga = Glb(after)
    mat = ga.doc['materials'][0]
    new_base = ga.image(ga.doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB')
    new_mask = ga.image(ga.doc['textures'][mat['extras']['openyamm_region_mask']['index']]['source'])
else:
    new_base = Image.open(f'{after}_basecolor.png').convert('RGB')
    new_mask = Image.open(f'{after}_region_mask.png')


def resample_old(img):
    """installed-layout image -> pass layout at the same surface points"""
    c, u = texlib.corresponding_uv(tid, bary, old_uv)
    out = np.zeros((S, S, img.shape[2]))
    out[c] = texlib.bilinear(img, u)
    return out


def mask_on(img_mask, old):
    m = np.asarray(img_mask.convert('RGBA'), np.float64) / 255
    if old:
        return resample_old(m)
    return np.stack([np.asarray(Image.fromarray((m[..., k] * 255).astype(np.uint8)).resize((S, S), Image.BILINEAR),
                                np.float64) / 255 for k in range(4)], -1)


m_old, m_new = mask_on(old_mask, True), mask_on(new_mask, False)


def skinlike(img):
    mx, mn = img.max(-1), img.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    return (img[..., 0] >= img[..., 1]) & (img[..., 1] >= 0.9 * img[..., 2]) & (sat > 0.12) & (sat < 0.5) & (mx > 110)


base_old = resample_old(np.asarray(old_base, np.float64))
base_new = np.asarray(new_base.resize((S, S), Image.BILINEAR), np.float64)
# skin: unmasked in both, skin-coloured in both maps (not vest, bracers, boots, lips, brows), outside eyes and mouth
skin = cov & (m_old[..., :2].max(-1) < 0.05) & (m_new[..., :2].max(-1) < 0.05) & (tp == 0) & skinlike(base_old) \
    & skinlike(base_new)
dist_band = None
# head-set boundary distance (euclidean to boundary vertices: the bands are narrow)
in_head = np.zeros(weld.max() + 1, bool)
in_body = np.zeros_like(in_head)
in_head[wtri[hf].ravel()] = True
in_body[wtri[~hf].ravel()] = True
wpos = np.zeros((weld.max() + 1, 3))
wpos[weld] = d['pos']
bpts = wpos[in_head & in_body]
from scipy.spatial import cKDTree  # noqa: E402
db = np.full((S, S), np.inf)
db[skin] = cKDTree(bpts).query(point[skin])[0]
zones = {
    'forehead': skin & hf[t] & (y > 1.655) & (y < 1.68) & (np.abs(x) < 0.025) & (nz > 0.5),
    'cheek_r': skin & hf[t] & (y > 1.59) & (y < 1.615) & (x < -0.02) & (x > -0.05) & (nz > 0.3),
    'cheek_l': skin & hf[t] & (y > 1.59) & (y < 1.615) & (x > 0.01) & (x < 0.04) & (nz > 0.3),
    'chin': skin & hf[t] & (y > 1.535) & (y < 1.555) & (np.abs(x + 0.005) < 0.02) & (nz > 0.3),
    'neck_head_side': skin & hf[t] & (db < 0.02) & (nz > 0.3),
    'neck_body_side': skin & ~hf[t] & (db < 0.02) & (y > 1.40) & (nz > 0.3),
    'upper_chest': skin & ~hf[t] & (y > 1.30) & (y < 1.38) & (nz > 0.6),
    'upper_arms': skin & ~hf[t] & (y > 1.15) & (y < 1.40) & (np.abs(x) > 0.2),
}
_, isl = np.unique(TQ.islands(uv, xyz), return_inverse=True)
isl = isl.ravel()
face_neck = hf & (piece == 0)
out = {}
tiers = [m['name'] for m in gb.doc['materials'][:9]]
for mi, name in enumerate(tiers):
    ramps = gb.doc['materials'][mi]['extras']['openyamm_region_ramps']
    eng_old = resample_old(bake(old_base, old_mask, ramps).astype(np.float64))
    eng_new = np.asarray(Image.fromarray(bake(new_base, new_mask, ramps)).resize((S, S), Image.BILINEAR), np.float64)
    row = {}
    for label, eng in (('installed', eng_old), ('pass', eng_new)):
        z = {k: np.round(np.average(eng[m], axis=0, weights=w[m]), 1).tolist() for k, m in zones.items()}
        means = np.array(list(z.values()))
        face_keys = ['forehead', 'cheek_r', 'cheek_l', 'chin']
        fm = np.array([z[k] for k in face_keys])
        res = {'zones': z,
               'face_spread': round(float(np.abs(fm[:, None] - fm[None]).max()), 1),
               'neck_step': round(float(np.abs(np.array(z['neck_head_side']) - np.array(z['neck_body_side'])).max()), 1),
               'head_vs_body_skin': round(float(np.abs(fm.mean(0) - np.array(z['upper_chest'])).max()), 1)}
        for reg, k in (('trousers', 0), ('hair', 1)):
            sel = cov & (m_old[..., k] > 0.5) & (m_new[..., k] > 0.5)
            res[reg] = np.round(np.average(eng[sel], axis=0, weights=w[sel]), 1).tolist()
        # chart seams on face and neck skin (pass layout charts; the installed map sampled at the same points)
        uniq, node, col = seam_level.corner_colours(eng, uv, wtri, isl)
        _, _, col_old = seam_level.corner_colours(base_old, uv, wtri, isl)
        _, _, col_new = seam_level.corner_colours(base_new, uv, wtri, isl)
        node_skin = skinlike(col_old) & skinlike(col_new)
        nch = isl.max() + 1
        vert = uniq // nch
        sel_node = np.zeros(len(uniq), bool)
        np.logical_or.at(sel_node, node[face_neck].ravel(), True)
        diffs = []
        order = np.argsort(vert)
        vs = vert[order]
        bounds = np.r_[0, np.nonzero(np.diff(vs))[0] + 1, len(vs)]
        for a, b in zip(bounds[:-1], bounds[1:]):
            g = order[a:b]
            g = g[sel_node[g] & node_skin[g]]
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    diffs.append(np.abs(col[g[i]] - col[g[j]]).max())
        diffs = np.array(diffs)
        res['face_neck_chart_seams'] = {'pairs': len(diffs), 'mean': round(float(diffs.mean()), 2),
                                        'p95': round(float(np.percentile(diffs, 95)), 2)}
        row[label] = res
    out[name] = row
    print(name, json.dumps({k: {kk: v[kk] for kk in ('face_spread', 'neck_step', 'head_vs_body_skin', 'trousers',
                                                     'hair', 'face_neck_chart_seams')} for k, v in row.items()}))
if len(sys.argv) > 3:
    json.dump(out, open(sys.argv[3], 'w'), indent=1)
