"""The Nobles' carapace atlas (2K), painted procedurally from work/carapace_layout.json (make_carapace.py: each
plate's outer surface fills its own rect, s across 0..1, r along 0..1; the rim shares the edge texels; inner surfaces,
glow strips and studs map to the dark block in the atlas corner). Concept fam_nobles.png: gilded grown chitin with
bone-ceramic inserts, black-violet resin joints and fine edges. Per texel, with e = the physical distance to the edge:
- gold (e < BAND; BAND = the spec's `insert` x the plate's half size, default 0.55): antique gold with chitin cells (Voronoi veins), a bright
  hairline at the very edge and a darker bevel;
- a black-violet resin groove (3 mm) between the band and the insert;
- the insert: bone-ivory ceramic with mottling and fine cell veins, slightly sunken;
- spikes: ivory with a gold collar at the root.
Outputs (textures/): nb_carapace_{basecolor,normal,metal_rough,region_mask}.png. ORM: R = AO stand-in, G = roughness
(gold 0.32, ivory 0.5, resin 0.6), B = 0 (metallic 0: the gold is painted). Region mask: R = gold, G = insert ivory and
spikes, B = painted glow, padded 4 px into the gutters; the dark block (resin) in no region. Args: none"""
import json, os
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, distance_transform_edt
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = json.load(open(os.path.join(HERE, 'work', 'carapace_layout.json')))
SPEC = json.load(open(os.path.join(HERE, 'scripts', 'carapace_noble.json')))
INSERT = {q['name']: q.get('insert', 0.55) for q in SPEC['plates']}      # ivory inlay: e > insert x the half size
N = L['atlas']; T = os.path.join(HERE, 'textures'); os.makedirs(T, exist_ok=True)
rng = np.random.default_rng(11)
base = np.zeros((N, N, 3)); height = np.zeros((N, N)); ao = np.ones((N, N)); rough = np.full((N, N), 0.6)
m_gd = np.zeros((N, N)); m_iv = np.zeros((N, N)); m_gl = np.zeros((N, N)); used = np.zeros((N, N), bool)
GOLD = np.array([214, 170, 84]) / 255.0; GOLD_D = np.array([132, 92, 40]) / 255.0; GOLD_H = np.array([250, 222, 150]) / 255.0
IVORY = np.array([228, 214, 182]) / 255.0; RESIN = np.array([40, 22, 40]) / 255.0; GLOWC = np.array([255, 140, 44]) / 255.0


def value_noise(h, w, cell, seed):
    r = np.random.default_rng(seed); g = r.random((h // cell + 3, w // cell + 3))
    yy, xx = np.mgrid[0:h, 0:w] / cell
    y0, x0 = yy.astype(int), xx.astype(int); fy, fx = yy - y0, xx - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx; b = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def cells(wm, hm, s, r, size, k):
    pts = rng.random((int(wm * hm / (size * size)) + 8, 2)) * [wm, hm]
    d, _ = cKDTree(pts).query(np.c_[(s * wm).ravel(), (r * hm).ravel()], k=2)
    return np.clip(1 - (d[:, 1] - d[:, 0]).reshape(s.shape) / (size * 0.45), 0, 1) ** 1.6


for k, (name, p) in enumerate(L['plates'].items()):
    x0, y0, w, h = p['rect']; wm, hm = p['size_m']
    yy, xx = np.mgrid[0:h, 0:w]
    s = (xx + 0.5) / w; r = 1 - (yy + 0.5) / h
    e = np.minimum(np.minimum(s, 1 - s) * wm, np.minimum(r, 1 - r) * hm)
    px = wm / w
    mot = 0.6 * value_noise(h, w, max(4, int(0.05 / px)), 10 + k) + 0.4 * value_noise(h, w, max(2, int(0.012 / px)), 50 + k)
    style = p.get('style', 'plate')
    glow = np.zeros((h, w))
    if style == 'spike':
        t_ = r
        gold = np.clip((0.12 - t_) / 0.03, 0, 1); groove = np.zeros_like(t_); ins = 1 - gold
        col = IVORY[None, None] * (0.84 + 0.16 * t_ + 0.08 * mot)[..., None]
        col = col * (1 - gold[..., None]) + GOLD * gold[..., None]
        hgt = 0.3 * gold + 0.05 * mot
        veins = np.zeros_like(t_)
    else:
        BAND = max(float(np.clip(0.16 * min(wm, hm), 0.008, 0.022)), INSERT.get(name, 0.55) * 0.5 * min(wm, hm))
        gold = np.clip((BAND + px - e) / (2 * px), 0, 1)
        groove = np.clip(1 - np.abs(e - BAND - 0.002) / (0.0018 + px), 0, 1)
        ins = (1 - gold) * (1 - groove)
        veins = cells(wm, hm, s, r, 0.022, k)
        gcol = GOLD[None, None] * (0.86 + 0.22 * mot)[..., None]
        gcol = gcol * (1 - 0.30 * veins)[..., None] + GOLD_D * 0.3 * veins[..., None]
        edge = np.clip(1 - e / max(0.0025, 1.5 * px), 0, 1)
        gcol = gcol * (1 - 0.6 * edge[..., None]) + GOLD_H * 0.6 * edge[..., None] * (e > px * 0.7)[..., None] + \
            GOLD_D * 0.6 * edge[..., None] * (e <= px * 0.7)[..., None]
        fine = cells(wm, hm, s, r, 0.009, 100 + k)
        icol = IVORY[None, None] * (0.88 + 0.14 * mot)[..., None] * (1 - 0.12 * fine)[..., None]
        icol = icol * (1 - 0.08 * np.clip(1 - (e - BAND) / 0.02, 0, 1))[..., None]        # warm shadow at the groove
        col = gcol * gold[..., None] + RESIN * groove[..., None] + icol * ins[..., None]
        hgt = 0.6 * gold - 1.0 * groove - 0.2 * veins * gold - 0.08 * fine * ins - 0.5 * np.clip(1 - e / 0.003, 0, 1) + 0.05 * mot
    for line in p.get('paint_glow', []):
        L_ = np.array(line); pts = np.c_[np.interp(np.linspace(0, len(L_) - 1, 60), range(len(L_)), L_[:, 0]) * wm,
                                         np.interp(np.linspace(0, len(L_) - 1, 60), range(len(L_)), L_[:, 1]) * hm]
        dd, _ = cKDTree(pts).query(np.c_[(s * wm).ravel(), (r * hm).ravel()])
        glow = np.maximum(glow, np.clip(1 - dd.reshape(h, w) / 0.004, 0, 1))
    for sx, sy in p.get('paint_studs', []):
        dd = np.hypot((s - sx) * wm, (r - sy) * hm); glow = np.maximum(glow, np.clip(1 - dd / 0.008, 0, 1) ** 0.6)
    glow = np.clip(glow * 1.5, 0, 1)
    col = col * (1 - glow[..., None]) + GLOWC * glow[..., None]
    sl = (slice(y0, y0 + h), slice(x0, x0 + w))
    base[sl] = col; height[sl] = hgt + 0.3 * glow
    ao[sl] = 1 - 0.40 * groove - 0.10 * veins - 0.2 * np.clip(1 - e / 0.004, 0, 1)
    rough[sl] = 0.32 * gold + 0.5 * ins + 0.6 * groove
    m_gd[sl] = gold * (1 - glow); m_iv[sl] = ins * (1 - glow); m_gl[sl] = glow
    used[sl] = True

base[N - 24:, N - 24:] = RESIN; used[N - 24:, N - 24:] = True; rough[N - 24:, N - 24:] = 0.7
dist, (iy, ix) = distance_transform_edt(~used, return_indices=True)
pad = (dist <= 4) & ~used
for arr in (base, height, ao, rough, m_iv, m_gd, m_gl):
    arr[pad] = arr[iy[pad], ix[pad]]
m_iv[N - 24:, N - 24:] = 0; m_gd[N - 24:, N - 24:] = 0; m_gl[N - 24:, N - 24:] = 0
m_iv, m_gd, m_gl = gaussian_filter(m_iv, 0.6), gaussian_filter(m_gd, 0.6), gaussian_filter(m_gl, 0.6)
base = np.clip(base, 20 / 255, 245 / 255)
Image.fromarray((base * 255).round().astype(np.uint8)).save(os.path.join(T, 'nb_carapace_basecolor.png'))
hs = gaussian_filter(height, 0.7) * 0.0012
pxm = 1.0 / L.get('texels_per_m', 1100)
gy, gx = np.gradient(hs, pxm)
nrm = np.dstack([-gx, gy, np.ones_like(hs)]); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
Image.fromarray(((nrm * 0.5 + 0.5) * 255).round().astype(np.uint8)).save(os.path.join(T, 'nb_carapace_normal.png'))
orm = np.dstack([np.clip(ao, 0, 1), np.clip(rough, 0, 1), np.zeros_like(ao)])
Image.fromarray((orm * 255).round().astype(np.uint8)).save(os.path.join(T, 'nb_carapace_metal_rough.png'))
mask = np.dstack([m_gd, m_iv, m_gl, np.zeros_like(m_iv)])
Image.fromarray((np.clip(mask, 0, 1) * 255).round().astype(np.uint8), 'RGBA').save(os.path.join(T, 'nb_carapace_region_mask.png'))
print('CARAPACETEX plates', len(L['plates']), 'atlas', N, 'used', round(float(used.mean()) * 100, 1), '%')
