#!/usr/bin/env python3
"""The sky-barges' and the celestial boat's textures, made in-script from shipped art (lane S, session 10).

work/tex/skybarge_trim.png (2048, shared by all five models): the hull, gilt and wood atlas.
work/tex/skybarge_cloth_<tint>.png (1024, one per tint): sail weave, canopy damask and the two glow images.

Sources (all shipped or the lane's own):
  - MM8's t66floor (x4 master): the hull, deck and inner-bulwark planks;
  - the Throne of Legends' wood atlas (xeen_throne_claude/work/throne_img0.png): the carved frieze, plain wood;
  - its gilded copy (xeen_throne_claude/work/tex/gold_base.png): the fluted gilt moulding, plain gilt, grey weave;
  - MM8's t66d01p2 (x4 master): the damask of the canopy (its red ground re-tinted per element).
Density: 2 texels per game unit everywhere (200 per Blender metre); the layout constants are shared with build.py
through layout.json. Usage: python3 textures.py"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
ROOT = PROJECT.parents[2]
OUT = PROJECT / 'work' / 'tex'
SRC = ROOT / 'assets_source/worlds'
THRONE = ROOT / 'level_generation/decorations/xeen_throne_claude/work'

# the element tints: ground of the cloth, its swirls, the glow
TINTS = {
    'fire': dict(ground=(196, 64, 24), swirl=(236, 186, 74), glow=(255, 122, 36)),
    'air': dict(ground=(222, 226, 232), swirl=(164, 176, 198), glow=(214, 232, 255)),
    'earth': dict(ground=(164, 104, 36), swirl=(238, 214, 150), glow=(255, 188, 72)),
    'water': dict(ground=(38, 132, 112), swirl=(222, 196, 112), glow=(72, 255, 206)),
    'boat': dict(ground=(206, 222, 240), swirl=(240, 236, 220), glow=(150, 200, 255)),
}

# trim atlas rows (pixels, top-down) and cloth atlas regions: x0, y0, x1, y1
TRIM = {
    'hull': (0, 0, 2048, 704),        # outer planks, u along the hull, v down from the frieze line
    'frieze': (0, 712, 2048, 840),    # 56 units of carved gilt band under the rail (112 px + 8 px each side)
    'deck': (0, 848, 2048, 1232),     # deck planks, v = distance from the centre line (mirrored halves)
    'inner': (0, 1240, 2048, 1368),   # the bulwark's inside, v normalised deck -> rail
    'mould': (0, 1376, 2048, 1440),   # fluted gilt moulding: rail cap, posts, mast hoops
    'panel': (0, 1456, 512, 1968),    # carved gilt panel (crates, transom)
    'gilt': (520, 1456, 1032, 1968),  # plain gilt
    'wood': (1040, 1456, 1552, 1968), # plain wood (mast, yard, gangplank, thwarts)
    'dark': (1560, 1456, 2048, 1968), # dark planks (the hull's underside near the keel, unused if not needed)
}
CLOTH = {
    'damask': (0, 0, 1024, 512),
    'weave': (0, 520, 640, 1016),
    'medal': (648, 520, 1016, 888),
    'strip': (648, 896, 1016, 1016),
}


def load(path, mode='RGB'):
    return Image.open(path).convert(mode)


def tile(img, w, h):
    out = Image.new('RGB', (w, h))
    for y in range(0, h, img.height):
        for x in range(0, w, img.width):
            out.paste(img, (x, y))
    return out


def put(atlas, region, img, pad=8):
    """Paste img into region and dilate its edge pixels `pad` px outward (mip gutter)."""
    x0, y0, x1, y1 = region
    img = img.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    a = np.asarray(img)
    big = np.pad(a, ((pad, pad), (pad, pad), (0, 0)), mode='edge')
    gx0, gy0 = max(0, x0 - pad), max(0, y0 - pad)
    ox, oy = gx0 - (x0 - pad), gy0 - (y0 - pad)
    gx1, gy1 = min(atlas.width, x1 + pad), min(atlas.height, y1 + pad)
    atlas.paste(Image.fromarray(big[oy:oy + gy1 - gy0, ox:ox + gx1 - gx0]), (gx0, gy0))
    atlas.paste(img, (x0, y0))


def grade(img, mul=1.0, add=0.0, sat=1.0):
    a = np.asarray(img).astype(np.float32)
    g = a.mean(axis=2, keepdims=True)
    a = g + (a - g) * sat
    a = a * mul + add
    return Image.fromarray(np.clip(a, 30, 243).astype(np.uint8))


def vfade(img, top=1.0, bottom=0.8):
    a = np.asarray(img).astype(np.float32)
    f = np.linspace(top, bottom, a.shape[0])[:, None, None]
    return Image.fromarray(np.clip(a * f, 30, 243).astype(np.uint8))


def trim_atlas():
    atlas = Image.new('RGB', (2048, 2048), (90, 60, 40))
    plank = load(SRC / 'mm8/textures_x4/t66floor.png').rotate(90, expand=True).resize((256, 256), Image.LANCZOS)
    img0 = load(THRONE / 'throne_img0.png')
    gold = load(THRONE / 'tex/gold_base.png')
    # hull: planks along the hull, a little lighter at the frieze line and darker toward the keel (the fade is
    # texture-borne: the static shader draws no vertex colour)
    put(atlas, TRIM['hull'], vfade(grade(tile(plank, 2048, 704), 1.08, sat=1.05), 1.05, 0.72))
    # a gilt wale 100 units under the frieze line (the hull's v runs down from that line, so it follows the sheer)
    wale = gold.crop((176, 210, 386, 980)).rotate(90, expand=True).resize((385, 20), Image.LANCZOS)
    atlas.paste(tile(wale, 2048, 20), (0, TRIM['hull'][1] + 4 + 200))
    # frieze: the carved panel (gold on dark wood) turned on its side, framed by thin gilt mouldings
    panel = img0.crop((412, 14, 712, 1006)).rotate(90, expand=True)          # ~992 x 300
    unit = panel.resize((372, 112), Image.LANCZOS)
    band = tile(unit, 2048, 112)
    put(atlas, TRIM['frieze'], band.resize((2048, 128)), pad=8)
    mould = gold.crop((176, 210, 386, 980)).rotate(90, expand=True)           # fluted gilt, ~770 x 210
    m = tile(mould.resize((385, 64), Image.LANCZOS), 2048, 64)
    put(atlas, TRIM['mould'], m)
    # gilt edges of the frieze row (8 px each) so the band reads framed
    fx0, fy0, fx1, fy1 = TRIM['frieze']
    edge = mould.resize((385, 10), Image.LANCZOS)
    atlas.paste(tile(edge, 2048, 10), (0, fy0))
    atlas.paste(tile(edge, 2048, 10), (0, fy1 - 10))
    # deck: the same planks scrubbed lighter
    put(atlas, TRIM['deck'], grade(tile(plank, 2048, 384), 1.25, 12, sat=0.8))
    # inner bulwark: darker planks
    put(atlas, TRIM['inner'], grade(tile(plank, 2048, 128), 0.8, sat=1.1))
    put(atlas, TRIM['panel'], img0.crop((412, 14, 712, 504)).resize((512, 512), Image.LANCZOS))
    put(atlas, TRIM['gilt'], gold.crop((4, 6, 150, 262)).resize((512, 512), Image.LANCZOS))
    put(atlas, TRIM['wood'], img0.crop((4, 6, 150, 262)).resize((512, 512), Image.LANCZOS))
    put(atlas, TRIM['dark'], grade(plank.resize((488, 512)), 0.6))
    return atlas


def recolour(img, ground, swirl):
    """Re-tint a cloth image: its luminance modulates `ground`; pixels brighter than the ground (damask swirls, the
    gold threads) blend toward `swirl`."""
    a = np.asarray(img).astype(np.float32) / 255.0
    lum = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    med = np.median(lum)
    rel = lum / max(med, 1e-3)
    sw = np.clip((lum - med) / max(lum.max() - med, 1e-3) * 2.2 - 0.25, 0, 1)[..., None]
    g = np.array(ground, np.float32)[None, None, :] * np.clip(rel, 0.55, 1.35)[..., None]
    s = np.array(swirl, np.float32)[None, None, :] * np.clip(0.85 + 0.3 * (lum - med), 0.7, 1.1)[..., None]
    out = g * (1 - sw) + s * sw
    return Image.fromarray(np.clip(out, 30, 243).astype(np.uint8))


def glow_medal(size, glow):
    """A glowing medallion: bright core, a ring, dark gaps, rays (the element's lamp), in-script."""
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    c = (size - 1) / 2
    r = np.hypot(x - c, y - c) / c
    ang = np.arctan2(y - c, x - c)
    core = np.clip(1.15 - r * 2.0, 0, 1)
    ring = np.exp(-((r - 0.72) / 0.07) ** 2)
    rays = (0.5 + 0.5 * np.cos(ang * 8)) * np.clip(1 - np.abs(r - 0.45) / 0.18, 0, 1) * 0.7
    v = np.clip(core + ring + rays, 0, 1)
    rim = np.clip((r - 0.86) / 0.1, 0, 1)                              # a gilt rim, not glowing
    col = np.array(glow, np.float32)[None, None, :] * (0.25 + 0.75 * v[..., None])
    gilt = np.array((200, 150, 60), np.float32)[None, None, :]
    out = col * (1 - rim[..., None]) + gilt * rim[..., None]
    return Image.fromarray(np.clip(out, 30, 255).astype(np.uint8))


def glow_strip(w, h, glow):
    y = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    v = np.clip(1.0 - np.abs(y) ** 1.6, 0, 1) * np.ones((1, w), np.float32)
    col = np.array(glow, np.float32)[None, None, :] * (0.35 + 0.65 * v[..., None])
    return Image.fromarray(np.clip(col, 30, 255).astype(np.uint8))


def cloth_atlas(tint):
    t = TINTS[tint]
    atlas = Image.new('RGB', (1024, 1024), t['ground'])
    damask = load(SRC / 'mm8/textures_x4/t66d01p2.png').resize((512, 512), Image.LANCZOS)   # 256 units a tile
    put(atlas, CLOTH['damask'], recolour(tile(damask, 1024, 512), t['ground'], t['swirl']))
    weave = load(THRONE / 'tex/gold_base.png').crop((724, 0, 1024, 1024)).resize((300, 1024), Image.LANCZOS)
    weave = tile(weave.crop((0, 0, 300, 600)), 640, 496)
    # the sail hangs in shade more than the canopy: its weave a little lighter than the ground
    put(atlas, CLOTH['weave'], grade(recolour(weave, t['ground'], t['swirl']), 1.18, 6))
    put(atlas, CLOTH['medal'], glow_medal(368, t['glow']))
    put(atlas, CLOTH['strip'], glow_strip(368, 120, t['glow']))
    return atlas


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    trim_atlas().save(OUT / 'skybarge_trim.png')
    for tint in TINTS:
        cloth_atlas(tint).save(OUT / f'skybarge_cloth_{tint}.png')
    (OUT / 'layout.json').write_text(json.dumps({'trim': TRIM, 'cloth': CLOTH, 'tints': TINTS}, indent=1))
    print('TEXTURES', sorted(p.name for p in OUT.glob('*.png')))


if __name__ == '__main__':
    main()
