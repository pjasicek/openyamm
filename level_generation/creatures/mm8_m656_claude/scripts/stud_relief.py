"""Raised studs and rivets for the Mercenary texture sets (2026-10-19, user review: the studs read as flat yellow dots).
Local texture work only: no geometry, UV or Meshy change. Reads a composed texture folder (default textures_v2) and
writes a copy with relief (default textures_v3):
- Studs are found in UV space: yellow/brass blobs (hue, saturation, value) on the armour pieces, kept when they are
  small, compact and clearly brighter than the leather ring around them. Belt, buckle, belt hardware, fur cuffs and
  forearm spikes are excluded by piece; cloth by hue.
- Each stud becomes a dome (distance to its edge, rounded), blended into the normal map (Meshy convention, +y down
  the image, as in the composed folders; swap_body_textures.py inverts G for the runtime atlas).
- ORM (R specular mask, G roughness, B zero): studs full specular and smooth, a little rougher at the rim.
- Base colour: one brass colour for every tier, lighter on top of the dome, darker at its rim, and a narrow contact
  shadow on the leather. The native studs (palette 657-659 entries 164/165) are the same olive-yellow in all three
  tiers, so the studs leave the armour region mask instead of taking the armour ramp's top stop.
- Gutters are padded again from the nearest island texel, as compose_mercenary.py does.
Usage: stud_relief.py [src folder] [dst folder]   writes <dst>/stud_report.json and work/studs/<part>_mask.png."""
import json, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as nd

P = Path(__file__).resolve().parents[1]
SRC = P / (sys.argv[1] if len(sys.argv) > 1 else 'textures_v2')
DST = P / (sys.argv[2] if len(sys.argv) > 2 else 'textures_v3')
OUT = P / 'work' / 'studs'
OUT.mkdir(parents=True, exist_ok=True)
DST.mkdir(exist_ok=True)
for f in SRC.iterdir():
    if f.is_file():
        shutil.copy2(f, DST / f.name)
if (SRC / 'props').is_dir():
    shutil.copytree(SRC / 'props', DST / 'props', dirs_exist_ok=True)

# Body: torso armour, gloves, boots, pauldrons, bracers, upper arms, skirt, elbows and skirt strips. Not the trousers
# (4), belt (12), buckle (24), fur cuffs (25, 26), forearm spikes and belt hardware (28-42).
BODY = [0, 2, 3, 6, 7, 9, 10, 11, 13, 14, 15, 16, 20, 23] + list(range(43, 84))
PARTS = {'body': ('UVMap', BODY, (8, 140)), 'head': ('HeadUV', [5], (3, 60))}
BRASS = np.array([0.62, 0.48, 0.22])
LUM = np.array([.2126, .7152, .0722])


def load(name, mode='RGB'):
    return np.asarray(Image.open(SRC / name).convert(mode), float) / 255


def save(a, name, mode=None):
    Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5), mode).save(DST / name)


report = {}
for part, (layer, pieces, (amin, amax)) in PARTS.items():
    r = np.load(P / 'work' / f'uvraster_{layer}.npz')
    pc = r['piece']
    cov = pc >= 0
    base = load(f'{part}_basecolor.png')
    normal = load(f'{part}_normal.png')
    orm = load(f'{part}_orm.png')
    mask = load(f'{part}_region_mask.png', 'RGBA')
    hsv = np.asarray(Image.fromarray(np.uint8(base * 255 + .5)).convert('HSV'), float) / 255
    lum = base @ LUM
    cand = (hsv[..., 0] > .07) & (hsv[..., 0] < .2) & (hsv[..., 1] > .3) & (hsv[..., 2] > .4) & np.isin(pc, pieces)
    lab, n = nd.label(cand)
    keep = np.zeros(n + 1, bool)
    stats = {'candidates': int(n), 'area': 0, 'shape': 0, 'contrast': 0}
    for i, sl in enumerate(nd.find_objects(lab), 1):
        comp = lab[sl] == i
        area = int(comp.sum())
        h, w = comp.shape
        if not amin <= area <= amax:
            stats['area'] += 1
            continue
        if max(h, w) > 2.0 * min(h, w) or area < 0.5 * h * w:
            stats['shape'] += 1
            continue
        y0, x0 = max(sl[0].start - 3, 0), max(sl[1].start - 3, 0)
        y1, x1 = min(sl[0].stop + 3, pc.shape[0]), min(sl[1].stop + 3, pc.shape[1])
        big = np.zeros((y1 - y0, x1 - x0), bool)
        big[sl[0].start - y0:sl[0].stop - y0, sl[1].start - x0:sl[1].stop - x0] = comp
        win = (slice(y0, y1), slice(x0, x1))
        ring = nd.binary_dilation(big, iterations=3) & ~nd.binary_dilation(big, iterations=1) & cov[win] & ~cand[win]
        inside = lum[win][big].mean()
        if ring.sum() < 4 or lum[win][ring].mean() > 0.6 * inside:
            stats['contrast'] += 1
            continue
        keep[i] = True
    studs = keep[lab]
    # Meshy's blobs are ragged; each stud is redrawn as the ellipse of the blob's second moments (same centre, area
    # and UV stretch), anti-aliased and clipped to the blob's own UV island. The leather under the old blob is filled
    # from the nearest leather texel first.
    island = nd.label(cov)[0]
    leather = cov & ~nd.binary_dilation(cand, iterations=1)
    near = nd.distance_transform_edt(~leather, return_distances=False, return_indices=True)
    old = nd.binary_dilation(studs, iterations=1) & cov
    base = base.copy()
    base[old] = base[tuple(near)][old]
    alpha = np.zeros(pc.shape)
    dome = np.zeros(pc.shape)
    height = np.zeros(pc.shape)
    objects = nd.find_objects(lab)
    for i in np.nonzero(keep)[0]:
        sl = objects[i - 1]
        ys, xs = np.nonzero(lab[sl] == i)
        ys, xs = ys + sl[0].start + .5, xs + sl[1].start + .5
        cy, cx = ys.mean(), xs.mean()
        cov2 = np.cov(np.stack([ys - cy, xs - cx])) + np.eye(2) * (1 / 12)
        val, vec = np.linalg.eigh(cov2)
        val = np.maximum(val, val.max() / 1.8 ** 2)
        semi = 2 * np.sqrt(val)
        semi *= np.sqrt(len(ys) / (np.pi * semi[0] * semi[1]))
        inv = vec @ np.diag(1 / semi ** 2) @ vec.T
        rad = int(np.ceil(semi.max())) + 2
        y0, y1 = max(int(cy) - rad, 0), min(int(cy) + rad + 1, pc.shape[0])
        x0, x1 = max(int(cx) - rad, 0), min(int(cx) + rad + 1, pc.shape[1])
        gy_, gx_ = np.mgrid[y0:y1, x0:x1] + .5
        d = np.stack([gy_ - cy, gx_ - cx], -1)
        rho = np.sqrt(np.einsum('...i,ij,...j->...', d, inv, d))
        own = island[y0:y1, x0:x1] == island[int(cy), int(cx)]
        a = np.clip((1 - rho) * semi.min() + 0.5, 0, 1) * own
        dm = np.sqrt(np.clip(1 - rho ** 2, 0, 1)) * own
        win = (slice(y0, y1), slice(x0, x1))
        alpha[win] = np.maximum(alpha[win], a)
        dome[win] = np.maximum(dome[win], dm)
        height[win] = np.maximum(height[win], dm * semi.min() * 0.9)
    studs = alpha > 0.5
    height = nd.gaussian_filter(height, 0.5)
    gy, gx = np.gradient(height)
    # +x along +u (columns); Meshy convention +y down the image, so the y slope is taken along rows unchanged.
    detail = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    detail /= np.linalg.norm(detail, axis=-1, keepdims=True)
    n1 = normal * 2 - 1
    mixed = np.stack([n1[..., 0] + detail[..., 0], n1[..., 1] + detail[..., 1], n1[..., 2] * detail[..., 2]], -1)
    mixed /= np.linalg.norm(mixed, axis=-1, keepdims=True)
    alpha *= cov
    # Base colour: brass shaded by the dome, a darker rim; contact shadow on the leather just outside.
    stud_rgb = BRASS[None, None] * (0.6 + 0.5 * dome[..., None])
    outside = nd.distance_transform_edt(alpha < 0.5)
    shadow = np.where((outside > 0) & (outside <= 2.5) & cov, 0.7 + 0.12 * (outside - 1), 1.0)
    out = base * np.clip(shadow, 0, 1)[..., None]
    out = out * (1 - alpha[..., None]) + stud_rgb * alpha[..., None]
    spec = orm[..., 0] * (1 - alpha) + alpha * 1.0
    rough = orm[..., 1] * (1 - alpha) + alpha * (0.3 + 0.18 * (1 - dome))
    orm_out = np.stack([spec, rough, np.zeros_like(spec)], -1)
    mask_out = mask * (1 - alpha[..., None])
    # Gutters take the nearest island texel again.
    idx = nd.distance_transform_edt(~cov, return_distances=False, return_indices=True)
    pad = tuple(idx)
    save(out[pad], f'{part}_basecolor.png')
    save((mixed * 0.5 + 0.5)[pad], f'{part}_normal.png')
    save(orm_out[pad], f'{part}_orm.png')
    save(mask_out[pad], f'{part}_region_mask.png', 'RGBA')
    preview = np.uint8(base * 255).copy()
    preview[studs] = [255, 0, 255]
    Image.fromarray(preview).save(OUT / f'{part}_mask.png')
    stats.update(studs=int(keep.sum()), texels=int(studs.sum()))
    report[part] = stats
    print(part, stats)
(DST / 'stud_report.json').write_text(json.dumps({'source': SRC.name, 'parts': report}, indent=2) + '\n')
