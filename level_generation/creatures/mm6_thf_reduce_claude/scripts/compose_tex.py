#!/usr/bin/env python3
"""Cloak and body texture sets from the two Meshy retextures (meshy/{cloak,body}_texture/*.glb), plus the kept head set.

- Maps: Meshy base colour, normal and metallic-roughness (2K) nearest-padded beyond each set's islands, then 1K.
  Metallic-roughness red is set to 1 (no baked AO in this pass).
- Tier region (one channel, `cloth`, as before): every cloak-set texel; on the body set the undershirt texels
  (hue 60-200, saturation >= 0.10) on the torso, sleeves and jerkin skirt UV regions. Colours come
  from the new texture (never the old mask; hue 60-200 since the body v2 retexture painted the sleeves olive). The cloth's luminance is matched to the installed tier-A cloth of the same
  kind (cloak/hood texels for the cloak set, undershirt texels for the body set; work/source_uv.json) by the rank of
  its smoothed luminance (folds and patches, not fine weave noise, take the dark tones), so the installed ramps
  recolour it the same way in every tier.
- Dagger swatches (steel blade, dark iron, leather grip) painted into empty cells of the body set, outside the mask;
  export_tex.py maps the dagger faces into them (textures/thf_dagger_swatches.json).
- textures/thf_ramps.json: the installed ramps for three materials (Thief_A body, ThiefCloak_A, ThiefHead_A).
Writes textures/thf_{body,cloak}_{basecolor,normal,metal_rough}_1k.png, thf_{body,cloak}_region_mask.png."""
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
INSTALLED = ROOT / 'assets_source/worlds/mm6/models/mm6_thf.glb'
OLD_RAMPS = HERE.parent / 'mm6_thf_claude/textures/thf_ramps.json'
T = HERE / 'textures'
SIZE, WORK = 1024, 2048
LUMA = np.array([0.2126, 0.7152, 0.0722])
BAND_SIGMA, DETAIL = 6.0, 0.8
SWATCHES = {'blade': (186, 188, 192), 'iron': (78, 78, 82), 'grip': (92, 58, 34)}
SHIRT_REGIONS = {'ArmL', 'ArmR', 'TorsoF', 'TorsoB', 'Skirt'}
MESHY_JOB = {'cloak': 'cloak_texture', 'body': 'body_texture_v3'}   # body v3: weighted layout, whole-thief upload
# 'installed' (user 2026-10-14): three body retextures smeared the belt and lower jerkin; the body keeps its maps
BODY_SOURCE = 'installed_col'   # installed body maps squeezed left, dagger column painted (build_master_tex.py)


def lin(s):
    return np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)


def enc(v):
    v = np.clip(v, 0, 1)
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * v ** (1 / 2.4) - 0.055)


def glb_doc(path):
    raw = path.read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), raw[28 + n:]


def image(doc, binary, index):
    v = doc['bufferViews'][doc['images'][index]['bufferView']]
    s = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(binary[s:s + v['byteLength']]))


def meshy_maps(path):
    doc, binary = glb_doc(path)
    mat = doc['materials'][0]
    pbr = mat.get('pbrMetallicRoughness', {})
    src = lambda ref: doc['textures'][ref['index']]['source']
    return {'base': image(doc, binary, src(pbr['baseColorTexture'])),
            'mr': image(doc, binary, src(pbr['metallicRoughnessTexture'])),
            'normal': image(doc, binary, src(mat['normalTexture']))}


def raster(tris, keep, size):
    img = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(img)
    for t in tris:
        if keep(t):
            d.polygon([(u * size, (1 - v) * size) for u, v in t['uv']], fill=255)
    return np.asarray(img) > 127


def pad(a, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return a[iy, ix]


def installed_cloth():
    """Linear luminance of the installed tier-A cloth texels (installed body set + mask, R > 0.9), split by the source's
    UV regions into cloak/hood and undershirt: the ramps put the wool on their dark stops and the shirt on their light
    ones, so each part is matched to its own installed range."""
    old = HERE.parent / 'mm6_thf_claude' / 'textures'
    base = np.asarray(Image.open(old / 'thf_a_basecolor_1k.png').convert('RGB'), np.float64) / 255
    mask = np.asarray(Image.open(old / 'thf_region_mask.png'), np.float64)[..., 0] / 255
    lum = lin(base) @ LUMA
    src = json.loads((HERE / 'work' / 'source_uv.json').read_text())
    names = src['regions']
    cloak = raster(src['tris'], lambda t: names[t['region']].startswith(('Cloak', 'Hood')), base.shape[0])
    shirt = raster(src['tris'], lambda t: names[t['region']] in SHIRT_REGIONS, base.shape[0])
    cloth = mask > 0.9
    return {'cloak': np.sort(lum[cloth & cloak]), 'body': np.sort(lum[cloth & shirt])}


def match(lin_base, core, target):
    lum = lin_base @ LUMA
    weight = core.astype(np.float64)
    smooth = ndimage.gaussian_filter(lum * weight, BAND_SIGMA) / np.maximum(ndimage.gaussian_filter(weight, BAND_SIGMA), 1e-6)
    src, low = lum[core], smooth[core]
    ranks = np.argsort(np.argsort(low)) / max(len(low) - 1, 1)
    matched = target[np.minimum((ranks * (len(target) - 1)).round().astype(int), len(target) - 1)]
    matched = matched * (src / np.maximum(low, 1e-5)) ** DETAIL
    lin_base[core] *= (matched / np.maximum(src, 1e-5))[:, None]
    return round(float(np.median(src)), 4), round(float(np.median(matched)), 4)


def swatch_cells(covered, cell=48):
    """Three empty cells (WORK pixels) away from every island, scanning from the top-right corner."""
    grown = ndimage.binary_dilation(covered, iterations=8)
    cells = []
    for y in range(0, WORK - cell, cell):
        for x in range(WORK - cell, 0, -cell):
            if not grown[y:y + cell, x:x + cell].any():
                cells.append((x, y))
                if len(cells) == 3:
                    return cells
    raise SystemExit('no empty cells for the dagger swatches')


def paint_daggers(img, info):
    """The rebuilt daggers' column (dagger_mesh.py layout), painted at WORK size: steel blade shaded across its width
    (bright cutting edge, edge bevel, darker flat, ridge highlight), a slightly lighter point, wrapped leather grip,
    dark iron guard and pommel with a highlight. Diffuse only (the thief has no specular), so the light is painted."""
    u0, u1 = info['dagger_col']
    rects = info['dagger_rects']
    x0, x1 = int(u0 * WORK), int(np.ceil(u1 * WORK))
    rng = np.random.default_rng(7)

    def rows(r):
        return int((1 - r[1]) * WORK), int(np.ceil((1 - r[0]) * WORK))
    # blade: s = 0 ridge .. 1 cutting edge; t = 0 guard .. 1 point
    y0, y1 = rows(rects['blade'])
    xs = (np.arange(x0, x1) + 0.5) / WORK
    s_ = np.abs((xs - u0) / (u1 - u0) / 1.0 * 2 - 1) * 1.05
    ts = 1 - ((np.arange(y0, y1) + 0.5) / WORK - (1 - rects['blade'][1])) / (rects['blade'][1] - rects['blade'][0])
    S, Tm = np.meshgrid(s_, ts)
    steel = np.where(S < 0.06, 205, np.where(S < 0.55, 150 + 25 * S, np.where(S < 0.92, 190 + 40 * (S - 0.55) / 0.37, 242)))
    steel = steel + 18 * np.clip(Tm - 0.7, 0, None) / 0.3 - 10 * np.clip(0.15 - Tm, 0, None) / 0.15
    steel = steel + rng.normal(0, 3.0, size=(1, steel.shape[1])) + rng.normal(0, 2.0, size=steel.shape)   # brushed
    blade = np.stack([steel * 0.97, steel * 0.99, steel * 1.03], -1)
    img[y0:y1, x0:x1] = np.clip(blade, 0, 255) / 255
    # grip: brown leather with a diagonal wrap
    y0, y1 = rows(rects['grip'])
    gy, gx = np.mgrid[y0:y1, x0:x1]
    phase = ((gx - x0) / max(x1 - x0, 1) * 1.2 + (gy - y0) / max(y1 - y0, 1) * 7.0) % 1.0
    shade = np.where(phase < 0.18, 0.55, 0.85 + 0.15 * np.sin(phase * np.pi))
    leather = np.array([92, 58, 34]) * shade[..., None] + rng.normal(0, 3, size=shade.shape)[..., None]
    img[y0:y1, x0:x1] = np.clip(leather, 0, 255) / 255
    # iron: guard and pommel
    y0, y1 = rows(rects['iron'])
    iy, ix = np.mgrid[y0:y1, x0:x1]
    hl = np.exp(-(((ix - x0) / max(x1 - x0, 1) - 0.5) ** 2) / 0.02)
    iron = 72 + 45 * hl + rng.normal(0, 3, size=hl.shape)
    img[y0:y1, x0:x1] = np.clip(np.stack([iron * 0.95, iron * 0.97, iron * 1.02], -1), 0, 255) / 255
    return x0, x1


def installed_col_set():
    """Installed body maps (thf_a_basecolor_1k etc.) squeezed into x < col_fill, the dagger column painted (2K, then
    1K). The cloth mask is the extended installed one (work/thf_installed_mask_ext.png), zero in the dagger column."""
    info = json.loads((HERE / 'work' / 'master_tex.json').read_text())
    old_t = HERE.parent / 'mm6_thf_claude' / 'textures'
    width = int(round(info['col_fill'] * WORK))

    def squeezed(path, mode='RGB'):
        img = Image.open(path)
        img = (img.convert('RGBA').split()[0] if mode == 'R' else img.convert(mode)).resize((width, WORK), Image.LANCZOS)
        a = np.zeros((WORK, WORK) + ((3,) if mode == 'RGB' else ()), np.float64)   # 'R': the mask channel alone
        a[:, :width] = np.asarray(img, np.float64) / 255
        a[:, width:] = a[:, width - 1:width]                   # edge texels repeated up to the column
        return a
    base = squeezed(old_t / 'thf_a_basecolor_1k.png')
    x0, x1 = paint_daggers(base, info)
    normal = squeezed(old_t / 'thf_normal_1k.png')
    normal[:, x0:x1] = (0.5, 0.5, 1.0)
    mr = squeezed(old_t / 'thf_metal_rough_1k.png')
    mr[:, x0:x1] = (1.0, 0.45, 0.0)
    for name, a in (('basecolor', base), ('normal', normal), ('metal_rough', mr)):
        Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS).save(
            T / f'thf_body_{name}_1k.png')
    mask = squeezed(HERE / 'work' / 'thf_installed_mask_ext.png', 'R')
    mask[:, width:] = 0.0
    sys.path.insert(0, str(HERE.parent / 'claude_shared'))
    import region_variants as R
    R.write_mask([mask], T / 'thf_body_region_mask.png', SIZE)


def bake_body_set():
    """Body maps from bake_body.py (work/bake_body.npz, 2K), padded, the dagger column painted, 1K."""
    info = json.loads((HERE / 'work' / 'master_tex.json').read_text())
    bake = np.load(HERE / 'work' / 'bake_body.npz')
    covered = bake['covered']
    base = pad(bake['base'], covered)
    x0, x1 = paint_daggers(base, info)
    Image.fromarray((np.clip(base, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS).save(
        T / 'thf_body_basecolor_1k.png')
    normal = pad(bake['normal'], covered)
    normal[:, x0:x1] = (0.5, 0.5, 1.0)
    Image.fromarray((np.clip(normal, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS).save(
        T / 'thf_body_normal_1k.png')
    mr = pad(bake['mr'], covered)
    mr[..., 0] = 1.0
    mr[:, x0:x1] = (1.0, 0.45, 0.0)
    Image.fromarray((np.clip(mr, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS).save(
        T / 'thf_body_metal_rough_1k.png')
    mask = pad(bake['mask'], covered)[..., 0]
    mask[:, x0 - 4:x1] = 0.0                                   # the dagger column takes no tier colour
    sys.path.insert(0, str(HERE.parent / 'claude_shared'))
    import region_variants as R
    R.write_mask([mask], T / 'thf_body_region_mask.png', SIZE)


def main():
    data = json.loads((HERE / 'work' / 'tex_uv.json').read_text())
    regions = data['regions']
    targets = installed_cloth()
    report = {}
    if BODY_SOURCE == 'installed_col':
        installed_col_set()
        report['body'] = 'installed maps (squeezed), daggers painted'
    if BODY_SOURCE == 'baked':
        bake_body_set()
        report['body'] = 'baked from the installed maps; daggers painted'
    if BODY_SOURCE == 'installed':
        # the body keeps the installed maps, mask and dagger swatches (body faces keep their installed UVs)
        old_t = HERE.parent / 'mm6_thf_claude' / 'textures'
        for src, dst in (('thf_a_basecolor_1k.png', 'thf_body_basecolor_1k.png'), ('thf_normal_1k.png', 'thf_body_normal_1k.png'),
                         ('thf_metal_rough_1k.png', 'thf_body_metal_rough_1k.png'), ('thf_region_mask.png', 'thf_body_region_mask.png'),
                         ('thf_dagger_swatches.json', 'thf_dagger_swatches.json')):
            (T / dst).write_bytes((old_t / src).read_bytes())
        # the installed mask missed thin crease lines on the sleeves (they kept the jade in tiers B/C, worse after the
        # reduction): installed mask + the shirt regions' texels of hue 60-200, closed over 2-texel gaps
        base = np.asarray(Image.open(T / 'thf_body_basecolor_1k.png').convert('RGB'), np.float64) / 255
        old_mask = np.asarray(Image.open(T / 'thf_body_region_mask.png'), np.float64)[..., 0] / 255
        src = json.loads((HERE / 'work' / 'source_uv.json').read_text())
        shirt = raster(src['tris'], lambda t: src['regions'][t['region']] in SHIRT_REGIONS, SIZE)
        hsv = np.asarray(Image.fromarray((base * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
        h, sat = hsv[..., 0] * 360, hsv[..., 1]
        cloth = shirt & (h >= 60) & (h <= 200) & (sat >= 0.10)
        cloth = ndimage.binary_closing(cloth | (shirt & (old_mask > 0.5)), iterations=2) & shirt
        # the sleeve regions are undershirt only (bracers and hands are their own regions): all cloth, so no crease or
        # seam texel keeps the jade (a render test with them forced to 1 removed the last zigzags)
        sleeves = raster(src['tris'], lambda t: src['regions'][t['region']] in ('ArmL', 'ArmR'), SIZE)
        cloth |= ndimage.binary_dilation(sleeves, iterations=2)
        weight = np.maximum(old_mask, ndimage.gaussian_filter(cloth.astype(np.float64), 0.7))
        # padded like the colour (nearest island texel into the gutters): the installed mask stopped at the island
        # edges, so filtering along every sleeve seam drew unrecoloured jade zigzags on tiers B/C
        islands = raster(src['tris'], lambda t: True, SIZE)
        weight = pad(weight[..., None], islands)[..., 0]
        # ...but not over the dagger swatches painted outside the islands (the padded mask tinted the blades green)
        sw = json.loads((T / 'thf_dagger_swatches.json').read_text())
        yy, xx = np.mgrid[0:SIZE, 0:SIZE]
        for u, v, r in sw.values():
            cx, cy, rad = u * SIZE, (1 - v) * SIZE, r * SIZE * 2.5 + 2
            weight[(xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2 <= rad * rad] = 0.0
        sys.path.insert(0, str(HERE.parent / 'claude_shared'))
        import region_variants as R
        R.write_mask([weight], T / 'thf_body_region_mask.png', SIZE)
        report['body'] = {'installed maps kept': True, 'mask_texels_before': int((old_mask > 0.5).sum()),
                          'after': int((weight > 0.5).sum())}
    for set_id, name in ((1, 'cloak'),) + (((0, 'body'),) if BODY_SOURCE == 'new' else ()):
        maps = meshy_maps(sorted((HERE / 'meshy' / MESHY_JOB[name]).glob('*.glb'))[-1])
        tris = [t for t in data['tris'] if t['set'] == set_id]
        covered = raster(tris, lambda t: True, WORK)
        base = np.asarray(maps['base'].convert('RGB').resize((WORK, WORK), Image.LANCZOS), np.float64) / 255
        if set_id == 1:
            cloth = covered.copy()
        else:
            shirt_faces = raster(tris, lambda t: regions[t['region']] in SHIRT_REGIONS, WORK)
            hsv = np.asarray(Image.fromarray((base * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
            h, s = hsv[..., 0] * 360, hsv[..., 1]
            # the installed rule took hue 95-200; Meshy also painted the sleeves and the torso under the mantle in
            # the cloak's olive (60-95), so the undershirt band starts at 60 (the leather stays below 60)
            cloth = shirt_faces & (h >= 60) & (h <= 200) & (s >= 0.10)
            cloth = ndimage.binary_opening(cloth, iterations=1)
        lin_base = lin(base)
        before, after = match(lin_base, cloth, targets[name])
        base = enc(lin_base)
        report[name] = {'cloth_texels': int(cloth.sum()), 'cloth_lum_median': [before, after]}
        rgb = pad(base, covered)
        if set_id == 0:
            cells = swatch_cells(covered)
            sw = {}
            for (x, y), (key, colour) in zip(cells, SWATCHES.items()):
                rgb[y:y + 48, x:x + 48] = np.array(colour) / 255
                sw[key] = [(x + 24) / WORK, 1 - (y + 24) / WORK, 12 / WORK]
            (T / 'thf_dagger_swatches.json').write_text(json.dumps(sw, indent=1) + '\n')
        T.mkdir(exist_ok=True)
        Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS).save(
            T / f'thf_{name}_basecolor_1k.png')
        normal = np.asarray(maps['normal'].convert('RGB').resize((WORK, WORK), Image.LANCZOS), np.float64)
        Image.fromarray(pad(normal, covered).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS).save(
            T / f'thf_{name}_normal_1k.png')
        mr = np.asarray(maps['mr'].convert('RGB').resize((WORK, WORK), Image.LANCZOS), np.float64)
        mr[..., 0] = 255
        Image.fromarray(pad(mr, covered).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS).save(
            T / f'thf_{name}_metal_rough_1k.png')
        weight = pad(cloth.astype(np.float64)[..., None], covered)[..., 0]
        weight = ndimage.gaussian_filter(weight, 1.0)
        sys.path.insert(0, str(HERE.parent / 'claude_shared'))
        import region_variants as R
        R.write_mask([weight], T / f'thf_{name}_region_mask.png', SIZE)
    old = json.loads(OLD_RAMPS.read_text())
    entry = old['materials'][0]
    old['materials'] = [dict(entry, base='Thief_A', prefix='Thief', mask='thf_body_region_mask.png'),
                        dict(entry, base='ThiefCloak_A', prefix='ThiefCloak', mask='thf_cloak_region_mask.png'),
                        dict(entry, base='ThiefHead_A', prefix='ThiefHead', mask='thf_head_region_mask.png')]
    (T / 'thf_ramps.json').write_text(json.dumps(old, indent=1) + '\n')
    (HERE / 'work' / 'compose_tex.json').write_text(json.dumps(report, indent=1) + '\n')
    print('COMPOSED', json.dumps(report))


if __name__ == '__main__':
    main()
