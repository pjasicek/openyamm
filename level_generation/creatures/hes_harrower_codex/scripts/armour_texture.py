"""hkr armour atlas (1K), painted procedurally from work/armour_layout.json (make_armour.py: every plate's outer
surface fills its own rect, s across 0..1, r along 0..1; the rim shares the edge texels; the inner surface, the glow
strips and the studs map to a dark block at the atlas corner). Concept: ivory chitin-ceramic with thin gold edges
(fam_troopers.png), so per texel with e = the physical distance to the plate's edge:
- ivory base (226, 214, 186) with two octaves of mottling and chitin cells (Voronoi F2 - F1 < 1.6 mm: fine darker
  veins), a faint warm yellowing toward the trim;
- an engraved groove 2.2-2.6 cm inside the edge (dark umber);
- the gold trim, e < GOLD (1.1 cm): brushed gold (204, 164, 82) with a darker outer 2 mm;
- normal map from a height field (bevel at the edge, the raised trim, the groove, the veins), OpenGL (+Y up);
- ORM: R = baked AO stand-in (groove, veins, trim shadow), G = roughness (ivory 0.55, gold 0.35), B = 0;
- region mask: R = ivory, G = gold trim, B = painted glow (minor plates' seams and studs, the buckler's studs), padded 4 px into the gutters; the dark block in no region;
- material classes: 11 (glazed chitin-ceramic, other) for ivory, 9 (metal) for the trim, 0 elsewhere.
Writes textures/hkr_armour_{basecolor,normal,metal_rough,region_mask,material_classes}.png. Args: none"""
import json, os
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, maximum_filter, grey_dilation
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = json.load(open(os.path.join(HERE, 'work', 'armour_layout.json')))
N = L['atlas']; T = os.path.join(HERE, 'textures'); os.makedirs(T, exist_ok=True)
GOLD, GROOVE0, GROOVE1 = 0.011, 0.022, 0.026
rng = np.random.default_rng(7)
base = np.zeros((N, N, 3)); height = np.zeros((N, N)); ao = np.ones((N, N)); rough = np.full((N, N), 0.55)
m_iv = np.zeros((N, N)); m_gd = np.zeros((N, N)); m_gl = np.zeros((N, N)); cls = np.zeros((N, N), np.uint8); used = np.zeros((N, N), bool)
IVORY = np.array([226, 214, 186]) / 255.0; GOLDC = np.array([204, 164, 82]) / 255.0; DARK = np.array([52, 40, 34]) / 255.0
UMBER = np.array([92, 72, 52]) / 255.0; GLOWC = np.array([255, 138, 40]) / 255.0
CARA = np.array([30, 18, 20]) / 255.0; CRED = np.array([120, 28, 22]) / 255.0


def value_noise(h, w, cell, seed):
    r = np.random.default_rng(seed); g = r.random((h // cell + 3, w // cell + 3))
    yy, xx = np.mgrid[0:h, 0:w] / cell
    y0, x0 = yy.astype(int), xx.astype(int); fy, fx = yy - y0, xx - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx; b = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


for k, (name, p) in enumerate(L['plates'].items()):
    x0, y0, w, h = p['rect']; wm, hm = p['size_m']
    yy, xx = np.mgrid[0:h, 0:w]
    s = (xx + 0.5) / w; r = 1 - (yy + 0.5) / h
    e = np.minimum(np.minimum(s, 1 - s) * wm, np.minimum(r, 1 - r) * hm)       # metres to the edge
    px = wm / w                                                                 # metres per texel
    # chitin cells: Voronoi in metres
    pts = rng.random((int(wm * hm / 0.0016) + 8, 2)) * [wm, hm]
    P = np.c_[(s * wm).ravel(), (r * hm).ravel()]
    d, _ = cKDTree(pts).query(P, k=2); vein = (d[:, 1] - d[:, 0]).reshape(h, w)
    veins = np.clip(1 - vein / 0.0016, 0, 1) ** 1.5
    mot = 0.6 * value_noise(h, w, max(4, int(0.05 / px)), 10 + k) + 0.4 * value_noise(h, w, max(2, int(0.012 / px)), 50 + k)
    col = IVORY[None, None] * (0.93 + 0.12 * mot)[..., None]
    col = col * (1 - 0.13 * veins)[..., None]
    warm = np.clip(1 - (e - GOLD) / 0.03, 0, 1)[..., None]
    col = col * (1 - 0.06 * warm) + np.array([0.02, 0.0, -0.03]) * warm
    groove = np.clip(1 - np.abs(e - (GROOVE0 + GROOVE1) / 2) / ((GROOVE1 - GROOVE0) / 2 + px), 0, 1)
    col = col * (1 - groove[..., None]) + UMBER * groove[..., None]
    gold = np.clip((GOLD + px - e) / (2 * px), 0, 1)
    gnoise = value_noise(h, w, max(2, int(0.006 / px)), 90 + k)
    gcol = GOLDC[None, None] * (0.9 + 0.18 * gnoise)[..., None] * (1 - 0.35 * np.clip(1 - e / 0.002, 0, 1))[..., None]
    col = col * (1 - gold[..., None]) + gcol * gold[..., None]
    hgt = 0.5 * gold - 0.8 * groove - 0.25 * veins - 0.6 * np.clip(1 - e / 0.003, 0, 1) + 0.05 * mot
    style = p.get('style', 'plate'); glow = np.zeros((h, w))
    if style == 'carapace':                       # tier B's black-and-red carapace (no region: the same on every tier)
        rim = np.clip(1 - e / 0.018, 0, 1)
        col = CARA[None, None] * (0.85 + 0.3 * mot)[..., None] * (1 - rim[..., None]) + CRED * (0.8 + 0.4 * mot)[..., None] * rim[..., None]
        col = col * (1 - 0.25 * veins)[..., None]
        hgt = 0.4 * rim - 0.3 * veins - 0.6 * np.clip(1 - e / 0.003, 0, 1) + 0.08 * mot; gold = np.zeros_like(e)
    elif style == 'buckler':
        xn, yn = s, 1 - r
        rho = 2 * np.sqrt((xn - 0.5) ** 2 + (yn - 0.5) ** 2); th = np.arctan2(-(yn - 0.5), xn - 0.5)
        R_ = p.get('radii', [0.30, 0.42, 0.62, 0.86, 1.0])
        col = IVORY[None, None] * (0.93 + 0.12 * mot)[..., None] * (1 - 0.13 * veins)[..., None]
        dark = (rho < R_[1]); gold = np.clip((rho - R_[3]) / 0.02, 0, 1)
        seg = np.clip(1 - np.abs(((th / (2 * np.pi / 8)) % 1) - 0.5) * 2 / 0.08, 0, 1) * ((rho > R_[1]) & (rho < R_[3]))
        col = np.where(dark[..., None], DARK * 1.2, col)
        col = col * (1 - seg[..., None]) + UMBER * seg[..., None]
        col = col * (1 - gold[..., None]) + GOLDC * (0.9 + 0.18 * mot)[..., None] * gold[..., None]
        studs = np.zeros_like(rho)
        for k in range(8):
            a_ = (k + 0.5) * 2 * np.pi / 8; cx, cy = 0.5 + 0.5 * 0.74 * np.cos(a_), 0.5 - 0.5 * 0.74 * np.sin(a_)
            studs = np.maximum(studs, np.clip(1 - np.hypot(xn - cx, yn - cy) / 0.035, 0, 1) ** 0.5)
        glow = np.maximum(glow, (studs > 0.2).astype(float))
        hgt = 0.5 * gold - 0.8 * seg - 0.4 * dark - 0.25 * veins + 0.05 * mot
        e = np.full_like(e, 1.0)
    elif style == 'spike':
        t_ = r; gold = np.clip((0.10 - t_) / 0.03, 0, 1)
        col = IVORY[None, None] * (0.86 + 0.14 * t_ + 0.08 * mot)[..., None]
        col = col * (1 - gold[..., None]) + GOLDC * gold[..., None]
        hgt = 0.4 * gold + 0.05 * mot
    if style in ('resin', 'cloth', 'hide', 'gold'):
        gold = np.zeros_like(e); groove = np.zeros_like(e)
        if style == 'resin':
            rib = .5 + .5 * np.cos(s * 6 * np.pi)
            col = np.array([.19,.105,.22]) * (.65 + .32 * rib + .14 * mot)[...,None]
            inlay = np.clip(1 - np.abs(s - .28) / .009, 0, 1)
            col = col * (1-inlay[...,None]) + GOLDC * inlay[...,None]
            hgt = .7 * rib - .2 * veins; gold = inlay
        elif style == 'cloth':
            weave = .025 * np.sin(xx * np.pi) * np.sin(yy * np.pi)
            col = np.array([.09,.065,.075]) * (.78 + .35*mot + weave)[...,None]
            hgt = .1 * mot + weave
        elif style == 'hide':
            grain = .5 + .5*np.sin(s*120 + 4*mot)
            col = np.array([.78,.72,.59]) * (.72 + .20*mot + .12*grain)[...,None]
            hgt = .18*grain + .1*mot
        else:
            col = GOLDC * (.83+.17*mot)[...,None];gold=np.ones_like(e);hgt=.1*mot
    for line in p.get('paint_glow', []):           # glow lines painted (no emissive geometry on the minor plates)
        L_ = np.array(line); pts = np.c_[np.interp(np.linspace(0, len(L_) - 1, 60), range(len(L_)), L_[:, 0]) * wm,
                                         np.interp(np.linspace(0, len(L_) - 1, 60), range(len(L_)), L_[:, 1]) * hm]
        dd, _ = cKDTree(pts).query(np.c_[(s * wm).ravel(), (r * hm).ravel()])
        glow = np.maximum(glow, np.clip(1 - dd.reshape(h, w) / 0.004, 0, 1))
    for sx, sy in p.get('paint_studs', []):
        dd = np.hypot((s - sx) * wm, (r - sy) * hm); glow = np.maximum(glow, np.clip(1 - dd / 0.008, 0, 1) ** 0.6)
    glow = np.clip(glow * 1.5, 0, 1) * (1 - gold)
    col = col * (1 - glow[..., None]) + GLOWC * glow[..., None]
    hgt = hgt + 0.3 * glow
    sl = (slice(y0, y0 + h), slice(x0, x0 + w))
    base[sl] = col; height[sl] = hgt; ao[sl] = 1 - 0.35 * groove - 0.12 * veins - 0.25 * np.clip(1 - e / 0.004, 0, 1)
    rough[sl] = 0.55 * (1 - gold) + 0.35 * gold
    if style in ('carapace','resin','cloth','hide'):
        rough[sl] = .78 if style in ('cloth','hide') else .4; m_gd[sl] = gold; m_iv[sl] = 0; m_gl[sl] = glow
    else:
        m_gd[sl] = gold * (1 - glow); m_iv[sl] = (1 - gold) * (1 - glow); m_gl[sl] = glow
    used[sl] = True
    cls[sl] = np.where(gold > 0.5, 9, 11)

# dark block (inner faces, glow strips, studs)
base[N - 24:, N - 24:] = DARK; used[N - 24:, N - 24:] = True; rough[N - 24:, N - 24:] = 0.8; cls[N - 24:, N - 24:] = 11
# pad colours and masks 4 px into the gutters (nearest used texel)
from scipy.ndimage import distance_transform_edt
dist, (iy, ix) = distance_transform_edt(~used, return_indices=True)
pad = (dist <= 4) & ~used
for arr in (base, height, ao, rough, m_iv, m_gd, m_gl):
    arr[pad] = arr[iy[pad], ix[pad]]
m_iv[N - 24:, N - 24:] = 0; m_gd[N - 24:, N - 24:] = 0; m_gl[N - 24:, N - 24:] = 0
m_iv, m_gd, m_gl = gaussian_filter(m_iv, 0.6), gaussian_filter(m_gd, 0.6), gaussian_filter(m_gl, 0.6)
base = np.clip(base, 12 / 255, 243 / 255)
alpha=np.ones((N,N))
for name in ('parts_cloth','parts_hide'):
    x,y,w,h=L['plates'][name]['rect'];yy,xx=np.mgrid[:h,:w]
    u=xx/w;t=yy/h
    rag=.78+.13*np.sin(u*19+1.7)+.055*np.sin(u*47+.8)
    left=.025+(.09+.15*(.5+.5*np.sin(t*61+2*np.sin(t*27))))*np.sqrt(t)
    right=.025+(.07+.19*(.5+.5*np.sin(t*53+1.8)))*np.sqrt(t)
    tears=np.zeros_like(t,dtype=bool)
    for cu,ct,ru,rt in ((.42,.29,.10,.024),(.61,.47,.13,.036),(.38,.65,.14,.035),(.65,.78,.12,.044)):
        tears |= np.abs((u-cu)/ru)+np.abs((t-ct)/rt)<1
    alpha[y:y+h,x:x+w]=((t<rag)&(u>left)&(u<1-right)&~tears).astype(float)
Image.fromarray((np.dstack([base,alpha])*255).round().astype(np.uint8),'RGBA').save(os.path.join(T,'hkr_armour_basecolor.png'))
# normal (OpenGL): image rows grow downward while v grows upward
hs = gaussian_filter(height, 0.7) * 0.0015                                      # metres of relief
pxm = 1.0 / L.get('texels_per_m', 850)
gy, gx = np.gradient(hs, pxm)
nrm = np.dstack([-gx, gy, np.ones_like(hs)]); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
Image.fromarray(((nrm * 0.5 + 0.5) * 255).round().astype(np.uint8)).save(os.path.join(T, 'hkr_armour_normal.png'))
spec = np.where(cls==9, .75, .24)
for name in ('parts_cloth','parts_hide'):
    x,y,w,h=L['plates'][name]['rect'];spec[y:y+h,x:x+w]=.04
orm = np.dstack([np.clip(spec, 0, 1), np.clip(rough, 0, 1), np.zeros_like(ao)])
Image.fromarray((orm * 255).round().astype(np.uint8)).save(os.path.join(T, 'hkr_armour_metal_rough.png'))
mask = np.dstack([m_iv, m_gd, m_gl, np.zeros_like(m_iv)])
Image.fromarray((np.clip(mask, 0, 1) * 255).round().astype(np.uint8), 'RGBA').save(os.path.join(T, 'hkr_armour_region_mask.png'))
Image.fromarray(cls, 'L').save(os.path.join(T, 'hkr_armour_material_classes.png'))
print('ARMOURTEX plates', len(L['plates']), 'atlas', N, 'texel density', L.get('texels_per_m'), 'per m; used',
      round(float(used.mean()) * 100, 1), '%')
