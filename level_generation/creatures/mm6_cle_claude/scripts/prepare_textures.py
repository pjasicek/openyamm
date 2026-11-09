#!/usr/bin/env python3
"""Runtime body maps and colour tiers for the cleric (CLAUDE_CREATURE_TEXTURES.md), from meshy/retexture_v1; adapted
from mm6_thf_claude/scripts/prepare_textures.py.

- Base colour: Meshy's map with the baked AO (work/ao_body.png, claude_shared/bake_creature_ao.py on rig_v2) graded in
  (claude_shared/grade_basecolor.py).
- Region mask (1024; R tunic, G legs, B cloak) + ramps. The native palettes 674/675/676 recolour exactly three index
  groups (scripts/native_pixels.py): the tunic and sleeves, the trousers and boots (also the thin mantle/hem piping
  and the chest emblem), and the grey collar, mantle and cloak. Texels: tunic = blue texels (hue 195-250, saturation
  >= 0.2) of the torso, sleeve and skirt UV regions (the gold cuffs and the belt stay fixed); legs = every texel of
  the leg and boot regions plus the dark trim texels (value < TRIM_V) of the cloak regions; cloak = the other cloak
  texels; the trim is repainted navy in the shared base (Meshy painted it near-black, the bottom of the legs ramp,
  black in every palette; the native trim is navy / green / white); trim components under TRIM_MIN texels and the
  collar's inner shadow are Meshy specks, painted over as cloak with its light/dark outliers (clean_cloak). Skin,
  hair, belt and gold keep their colour in every tier. Ramps: claude_shared/native_shading.transfer_ramps
  from the aligned native pixels (for each stop the 675 pixels nearest in luminance, read in 674/675/676, x ALBEDO).
- Staff swatches: bright gold (finial, crossbars, knob) and darker gold (shaft), painted into empty atlas cells
  (outside every UV island and the mask); export_runtime.py maps the staff faces into them
  (textures/cle_staff_swatches.json).
- Normal 1024, ORM 1024 (R baked AO, G roughness, B metallic), material classes 1024.
Writes into textures/: cle_a_basecolor.png (2K), cle_a_basecolor_1k.png, cle_normal_1k.png, cle_metal_rough_1k.png,
cle_region_mask.png, cle_ramps.json, cle_material_classes.png, cle_staff_swatches.json."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import native_shading as NS
import region_variants as R

T = HERE / 'textures'
M = HERE / 'meshy' / 'retexture_v1'
TIERS = {'cle_a': 674, 'cle_b': 675, 'cle_c': 676}
ALBEDO = {'tunic': 1.0, 'legs': 1.0, 'cloak': 1.0}
N = 1024
TUNIC_REGIONS = {'TorsoF', 'TorsoB', 'ArmL', 'ArmR', 'SkirtF', 'SkirtB'}
LEG_REGIONS = {'LegLF', 'LegLB', 'LegRF', 'LegRB', 'BootL', 'BootR'}
CLOAK_REGIONS = {'Collar', 'Mantle', 'Mantlei', 'CloakB', 'CloakBi', 'CloakL', 'CloakLi', 'CloakR', 'CloakRi'}
TRIM_V = 0.33
TRIM_MIN = 1000          # texels at 2K: the piping and emblem components are larger, Meshy's specks smaller
OUTLIER = 0.08
# Sprite contrast (NATIVE_SHADING_TRANSFER.md: the height profile already matched within about 0.05, the spread did
# not): the inside of the cloak is near black in the sprites, and the cloth's light-to-dark range is wider.
INNER_SHADE = 0.5        # inner cloak and mantle luminance factor (median 0.54 -> 0.27), on the faces cloak_sides.py
                         # finds on the inside (the island labels mix the sides near the hem and front edges)
CONTRAST = {'tunic': 1.6, 'cloak': 1.8}   # stretch of the cloth's broad shading about its median, detail kept
SKIRT_REGIONS = {'SkirtF', 'SkirtB'}
SKIRT_SIGMA = 24         # texels at 2K (smooth_skirt)
LINING_SHADE = 0.75      # skirt lining luminance against the outside's median (shade_lining)
POUCH_R, SHADOW_K = 0.07, 0.6   # pouch shadow on the tunic (relight_pouch_shadow)
AO_STRENGTH = 0.6        # grade_basecolor.py --ao-strength below
GREY_S = 0.4             # unpainted (grey or pale) tunic texels, repainted by fill_unpainted
SWATCHES = {'gold': (222, 178, 64), 'gold_dark': (168, 118, 36)}
T.mkdir(exist_ok=True)


def raster(regions_wanted, layout, size):
    img = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(img)
    for r, pts in layout['faces']:
        if layout['regions'][r] in regions_wanted:
            d.polygon([(u * size, (1 - v) * size) for u, v in pts], fill=255, outline=255)
    return np.asarray(img) > 0


def raster_faces(indices, layout, size):
    img = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(img)
    for i in indices:
        d.polygon([(u * size, (1 - v) * size) for u, v in layout['faces'][i][1]], fill=255, outline=255)
    return np.asarray(img) > 0


def hsv_of(rgb):
    hsv = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]


def soft(m):
    return np.clip(ndimage.gaussian_filter(m.astype(np.float64), 1.0), 0, 1)


def fill_unpainted(base, layout):
    """Meshy left the tunic grey or washed-out pale blue where none of its views saw it (under the arms, the flanks
    behind the cloak, the back of the torso); the tunic mask took only blue texels and its ramp reads luminance, so
    these stayed light grey or near white in every tier and showed when the library Attack lifts the staff arm (user
    review 2026-10-14 (2)). Unpainted = tunic-region texels with saturation < GREY_S that are not gold or skin. They
    take the tunic's median colour at the broad luminance of the painted tunic around them (blurred over the painted
    texels only), times their own luminance relative to their local mean, so Meshy's folds stay. Returns the count."""
    S = base.shape[0]
    h, s, v = hsv_of(base)
    shell = raster(TUNIC_REGIONS, layout, S)
    warm = (h > 10) & (h < 65) & (s > 0.25)
    grey = shell & (s < GREY_S) & ~warm
    painted = shell & (h > 195) & (h < 250) & (s >= GREY_S)
    lum = NS.srgb_luminance(base)
    colour = np.median(base[painted], 0); colour_lum = float(NS.srgb_luminance(colour[None])[0])

    def blur_over(values, mask, sigma):
        return ndimage.gaussian_filter(values * mask, sigma) / np.maximum(ndimage.gaussian_filter(
            mask.astype(np.float64), sigma), 1e-6)

    target = blur_over(lum, painted, 30)
    detail = np.clip(lum / np.maximum(blur_over(lum, grey, 10), 1e-3), 0.8, 1.2)
    base[grey] = np.clip(colour[None] * (target[grey] * detail[grey] / colour_lum)[:, None], 0, 1)
    return int(grey.sum())


def relight_pouch_shadow(base, layout):
    """The pouch's baked AO (graded into the base colour at AO_STRENGTH) and Meshy's painted pouch shadow darken the
    tunic behind the belt pouch; the library Attack swings the pouch off it and showed dark shards under it (user
    review 2026-10-14 (2)). On the tunic texels of the triangles behind the pouch (work/uv3d.npz: Torso triangles
    within POUCH_R of a pouch triangle, the pouch = Belt triangles below the belt band) the AO grading is undone, then
    texels still darker than SHADOW_K x the broad luminance of the tunic around them are lifted to it, keeping their
    colour and detail. Returns the relit texel count."""
    S = base.shape[0]
    d = np.load(HERE / 'work' / 'uv3d.npz')
    part = d['parts'][d['part']]; cen = d['xyz'].mean(1)
    belt = part == 'Belt'
    pouch = cen[belt & (cen[:, 2] < np.percentile(cen[belt, 2], 30))]
    near = np.linalg.norm(cen[:, None] - pouch[None], axis=2).min(1) < POUCH_R
    behind = cen[:, 1] > pouch[:, 1].min() - 0.005                     # the character faces -Y
    img = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(img)
    for tri in d['uv'][(part == 'Torso') & near & behind]:
        dr.polygon([(u * S, (1 - v) * S) for u, v in tri], fill=255, outline=255)
    zone = (np.asarray(img) > 0) & raster(TUNIC_REGIONS, layout, S)
    ao = np.asarray(Image.open(HERE / 'work' / 'ao_body.png').convert('L').resize((S, S), Image.BILINEAR),
                    np.float64) / 255
    base[zone] = np.clip(base[zone] / (1.0 - AO_STRENGTH * (1.0 - np.maximum(ao[zone], 0.05)))[:, None], 0, 1)
    lum = NS.srgb_luminance(base)
    tunic = raster(TUNIC_REGIONS, layout, S) & ~zone
    broad = ndimage.gaussian_filter(lum * tunic, 30) / np.maximum(ndimage.gaussian_filter(tunic.astype(np.float64),
                                                                                          30), 1e-6)
    dark = zone & (lum < SHADOW_K * broad)
    base[dark] = np.clip(base[dark] * (broad[dark] / np.maximum(lum[dark], 0.02))[:, None], 0, 1)
    return int(dark.sum())


def lining_mask(S):
    """texels of the skirt lining (work/skirt_sides.json from skirt_shell.py: the inner faces' UV polygons)"""
    img = Image.new('L', (S, S), 0); d = ImageDraw.Draw(img)
    for poly in json.loads((HERE / 'work' / 'skirt_sides.json').read_text())['inner_uv']:
        d.polygon([(u * S, (1 - v) * S) for u, v in poly], fill=255, outline=255)
    return np.asarray(img) > 0


def shade_lining(base, layout):
    """The skirt's inside shows at the slits and where the walk folds the hem and the side of the panel over (the
    source skinning folds 1-6 outer faces per walk frame, unreduced too); Meshy painted it lighter than the outside and
    it read as light shards (user review 2026-10-14 (3)). The lining faces are now removed at export; the hem's rim
    faces (the cloth's thickness) still use these texels and read as a light band under the hem at the outside's
    median, so the lining texels take the outside's median colour at LINING_SHADE x its median luminance (a shadowed
    edge), with their own fine detail. Returns the lining texel count."""
    S = base.shape[0]
    lining = lining_mask(S) & raster(SKIRT_REGIONS, layout, S)
    outside = raster(SKIRT_REGIONS, layout, S) & ~lining
    lum = NS.srgb_luminance(base)

    def blur_in(values, m, sigma):
        return ndimage.gaussian_filter(values * m, sigma) / np.maximum(ndimage.gaussian_filter(m.astype(np.float64),
                                                                                               sigma), 1e-6)

    colour = np.median(base[outside], 0); colour_lum = float(NS.srgb_luminance(colour[None])[0])
    target = LINING_SHADE * float(np.median(lum[outside]))
    detail = np.clip(lum / np.maximum(blur_in(lum, lining, 2.0 * S / 2048), 1e-3), 0.85, 1.15)
    base[lining] = np.clip(colour[None] * (target * detail[lining] / colour_lum)[:, None], 0, 1)
    return int(lining.sum())


def smooth_skirt(base, layout):
    """Meshy baked sharp-edged dark and light blotches into the tunic skirt (per-triangle patches, 3-6 cm); the tunic
    ramp maps luminance to colour and native_contrast stretches it 1.6x, so they showed as dark and pale shards on the
    front of the robe (user review 2026-10-14 (3)). Within the skirt islands only (normalised blur, no bleed across
    seams) the luminance becomes its blur at SKIRT_SIGMA texels (the broad folds) times the fine detail (the ratio to
    a 2-texel blur, clamped to +-15 %), colour kept. Returns the skirt texel count."""
    S = base.shape[0]
    m = raster(SKIRT_REGIONS, layout, S) & ~lining_mask(S)

    def blur_in(values, sigma):
        return ndimage.gaussian_filter(values * m, sigma) / np.maximum(ndimage.gaussian_filter(m.astype(np.float64),
                                                                                               sigma), 1e-6)

    lum = NS.srgb_luminance(base)
    want = blur_in(lum, SKIRT_SIGMA * S / 2048) * np.clip(lum / np.maximum(blur_in(lum, 2.0 * S / 2048), 1e-3),
                                                         0.85, 1.15)
    base[m] = np.clip(base[m] * (want[m] / np.maximum(lum[m], 1e-3))[:, None], 0, 1)
    return int(m.sum())


def region_weights(base, layout):
    S = base.shape[0]
    h, s, v = hsv_of(base)
    tunic_shell = ndimage.binary_dilation(raster(TUNIC_REGIONS, layout, S), iterations=2)
    blue = (h > 195) & (h < 250) & (s >= 0.2)
    tunic = ndimage.binary_closing(ndimage.binary_opening(tunic_shell & blue, iterations=1), iterations=1)
    cloak_shell = ndimage.binary_dilation(raster(CLOAK_REGIONS, layout, S), iterations=2)
    trim = cloak_shell & (v < TRIM_V)
    trim = ndimage.binary_closing(trim, iterations=1)
    # only the piping and the emblem are trim: small dark specks in Meshy's cloak paint and the collar's inner shadow
    # took the legs ramp (white in tier C) as spots on the mantle and collar; they become cloak and are painted over
    lab, n = ndimage.label(trim)
    sizes = ndimage.sum(trim, lab, range(1, n + 1))
    collar = ndimage.mean(raster({'Collar'}, layout, S), lab, range(1, n + 1))
    keep = np.flatnonzero((sizes >= TRIM_MIN * (S / 2048) ** 2) & (collar < 0.5)) + 1
    specks = trim & ~np.isin(lab, keep)
    trim &= ~specks
    legs = ndimage.binary_dilation(raster(LEG_REGIONS, layout, S), iterations=2) | trim
    cloak = cloak_shell & ~trim
    wt, wl, wc = soft(tunic), soft(legs & ~tunic), soft(cloak & ~tunic)
    total = np.maximum(wt + wl + wc, 1.0)
    return wt / total, wl / total, wc / total, trim, specks


def clean_cloak(base, cloak, specks):
    """Paint the trim specks over with the surrounding cloth, then replace isolated light or dark texels of the cloak
    (|luminance - local median| > OUTLIER) by the local median: the cloak ramp maps luminance to colour, so Meshy's
    blotches read as spots in every tier."""
    hole = ndimage.binary_dilation(specks, iterations=2)
    source = cloak & ~hole
    fill = np.stack([ndimage.gaussian_filter(base[..., c] * source, 4) for c in range(3)], -1)
    fill /= np.maximum(ndimage.gaussian_filter(source.astype(np.float64), 4), 1e-6)[..., None]
    base[hole & cloak] = fill[hole & cloak]
    median = np.stack([ndimage.median_filter(base[..., c], size=9) for c in range(3)], -1)
    lum, lum_median = NS.srgb_luminance(base), NS.srgb_luminance(median)
    outliers = cloak & (np.abs(lum - lum_median) > OUTLIER)
    base[outliers] = median[outliers]
    return int((hole & cloak).sum()), int(outliers.sum())


def swatch_cells(layout, size=N, cell=24, count=2):
    """Empty cells (no island within 6 texels) in the 1K atlas, scanning from the bottom-right corner."""
    occ = ndimage.binary_dilation(raster(set(layout['regions']), layout, size), iterations=6)
    cells = []
    for y in range(size - cell - 4, 0, -cell):
        for x in range(size - cell - 4, 0, -cell):
            if not occ[y:y + cell, x:x + cell].any() and not any(abs(x - cx) < cell and abs(y - cy) < cell
                                                                  for cx, cy in cells):
                cells.append((x, y))
            if len(cells) == count:
                return cells, cell
    raise SystemExit('no empty atlas cells for the staff swatches')


def native_contrast(base, layout, regions):
    """Carry the sprites' contrast onto the cloth: darken the inner cloak shell by INNER_SHADE, then stretch each
    region's broad shading (luminance blurred inside the region; the outer cloth only) about its median by CONTRAST,
    keeping the texel's ratio to that blur as detail. Returns {region: (p10, p50, p90) luminance after}."""
    sides = json.loads((HERE / 'work' / 'cloak_sides.json').read_text())
    inner = raster_faces(sides['inner'], layout, base.shape[0]) & regions['cloak']
    base[inner] *= INNER_SHADE
    out = {}
    for name, region in regions.items():
        mask = region & ~inner
        lum = NS.srgb_luminance(base)
        weight = ndimage.gaussian_filter(mask.astype(np.float64), 12)
        broad = ndimage.gaussian_filter(lum * mask, 12) / np.maximum(weight, 1e-6)
        mid = np.median(broad[mask])
        stretched = np.clip(mid + (broad - mid) * CONTRAST[name], 0.02, 0.95)
        gain = np.where(mask, stretched / np.maximum(broad, 1e-3), 1.0)
        base[mask] = np.clip(base[mask] * gain[mask][:, None], 0, 1)
        out[name] = [round(float(v), 3) for v in np.percentile(NS.srgb_luminance(base[region]), (10, 50, 90))]
    return out


def main():
    layout = json.loads((HERE / 'work' / 'uv_layout.json').read_text())
    raw = T / 'cle_a_basecolor_raw.png'
    Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').save(raw)
    subprocess.run([sys.executable, str(HERE.parent / 'claude_shared' / 'grade_basecolor.py'), '--ao',
                    str(HERE / 'work' / 'ao_body.png'), '--ao-strength', str(AO_STRENGTH), '--local', '0.4', '--contrast', '1.05',
                    '--saturation', '1.0', str(raw)], check=True)
    base = np.asarray(Image.open(T / 'cle_a_basecolor_raw_graded.png').convert('RGB'), np.float64) / 255
    S2 = base.shape[0]
    unpainted = fill_unpainted(base, layout)
    pouch_shadow = relight_pouch_shadow(base, layout)
    lining = shade_lining(base, layout)
    smooth_skirt(base, layout)
    wt, wl, wc, trim, specks = region_weights(base, layout)
    cleaned = clean_cloak(base, wc > 0.9, specks)
    contrast = native_contrast(base, layout, {'tunic': wt > 0.9, 'cloak': wc > 0.9})
    # the trim (mantle/hem piping, chest emblem) is near-black in Meshy's paint, the bottom of the legs ramp, where
    # every palette is black; the native trim is navy / green / white (the legs' bright end): repaint it navy
    legs_only = (wl > 0.9) & ~trim
    lum = NS.srgb_luminance(base[legs_only])
    navy = np.median(base[legs_only][(lum > np.percentile(lum, 80)) & (lum < np.percentile(lum, 95))], 0)
    base[trim] = navy * (0.85 + 0.3 * np.clip(NS.srgb_luminance(base[trim]) / 0.2, 0, 1))[:, None]
    pixels = np.load(HERE / 'work' / 'native_shading' / 'pixels.npz')
    weights = {'tunic': wt, 'legs': wl, 'cloak': wc}
    ramps = NS.transfer_ramps(base, weights, pixels, {k: k for k in weights}, TIERS, reference=675, gain=ALBEDO)
    # edge padding: Meshy's light-grey fill between the islands sat under the soft region mask, so the ramps read it
    # near their brightest stop and mipmapping drew light lines along every seam; each texel outside the islands now
    # repeats its nearest island texel (colour and region weights; after the ramps, which read only real texels)
    islands = raster(set(layout['regions']), layout, S2)
    _, (ny, nx) = ndimage.distance_transform_edt(~islands, return_indices=True)
    outside = ~islands
    base[outside] = base[ny[outside], nx[outside]]
    for w in (wt, wl, wc):
        w[outside] = w[ny[outside], nx[outside]]
    # the skirt's inside (skirt_shell.add_inside, user review 2026-10-14 (3)): a flat tunic cell at LINING_SHADE of the
    # outside's median luminance, tunic-masked so every tier ramps it
    tun = (wt > 0.9) & islands
    tc = np.median(base[tun], 0); tc = tc * LINING_SHADE * float(np.median(NS.srgb_luminance(base[tun]))) / \
        float(NS.srgb_luminance(tc[None])[0])
    swatches = dict(SWATCHES, lining=tuple(np.clip(tc * 255, 0, 255)))
    cells, cell = swatch_cells(layout, count=len(swatches))
    sw = {}
    k = S2 // N
    for (x, y), (name, rgb) in zip(cells, swatches.items()):
        base[y * k:(y + cell) * k, x * k:(x + cell) * k] = np.array(rgb) / 255
        for w in weights.values():
            w[y * k:(y + cell) * k, x * k:(x + cell) * k] = 0
        if name == 'lining':
            wt[y * k:(y + cell) * k, x * k:(x + cell) * k] = 1
        sw[name] = [(x + cell / 2) / N, 1 - (y + cell / 2) / N, (cell / 4) / N]     # u, v centre, half size
    (T / 'cle_staff_swatches.json').write_text(json.dumps(sw, indent=1) + '\n')
    report = {name: int(((w > 0.9) & islands).sum()) for name, w in weights.items()}
    report['cloak_cleaned'] = {'specks': cleaned[0], 'outliers': cleaned[1]}
    report['tunic_unpainted_filled'] = unpainted
    report['pouch_shadow_relit'] = pouch_shadow
    report['skirt_lining_shaded'] = lining
    report['contrast_p10_50_90'] = contrast
    report.update({'ranges': {name: r['range'] for name, r in zip(weights, ramps['cle_b'])}, 'swatches': sw})
    Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).save(T / 'cle_a_basecolor.png', optimize=True)
    Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).resize((N, N), Image.LANCZOS).save(
        T / 'cle_a_basecolor_1k.png', optimize=True)
    nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((N, N), Image.LANCZOS)).copy()
    rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((N, N), Image.LANCZOS)).copy()
    metal = np.asarray(Image.open(M / 'texture_urls_0_metallic.png').convert('L').resize((N, N), Image.LANCZOS)).copy()
    ao = np.asarray(Image.open(HERE / 'work' / 'ao_body.png').convert('L').resize((N, N), Image.LANCZOS)).copy()
    for (x, y), name in zip(cells, swatches):
        nrm[y:y + cell, x:x + cell] = (128, 128, 255); ao[y:y + cell, x:x + cell] = 255
        rough[y:y + cell, x:x + cell] = 90 if name != 'lining' else int(np.median(rough)); metal[y:y + cell, x:x + cell] = 0
    Image.fromarray(nrm).save(T / 'cle_normal_1k.png', optimize=True)
    Image.fromarray(np.stack([ao, rough, metal], -1)).save(T / 'cle_metal_rough_1k.png', optimize=True)
    R.write_mask([wt, wl, wc], T / 'cle_region_mask.png', size=N)
    config = {'variants': list(TIERS),
              'materials': [{'base': 'Cleric_A', 'prefix': 'Cleric', 'mask': 'cle_region_mask.png',
                             'regions': list(weights), 'palettes': TIERS, 'ramps': ramps, 'report': report}]}
    (T / 'cle_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    small = lambda m: np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((N, N), Image.BILINEAR)) > 127
    cls = np.zeros((N, N), np.uint8)
    cls[raster(set(layout['regions']), layout, N)] = 1                 # skin by default (hands, neck)
    cls[raster({'Hair'}, layout, N)] = 2
    cls[raster({'Belt'}, layout, N)] = 8
    for w in weights.values():
        cls[small(w)] = 8
    for (x, y), name in zip(cells, swatches):
        cls[y:y + cell, x:x + cell] = 9 if name != 'lining' else 8
    Image.fromarray(cls, 'L').save(T / 'cle_material_classes.png')
    # review: base, the three regions, and tier previews (exact shader ramp application)
    prev = [np.clip(base, 0, 1)]
    prev.append(np.stack([wt, wl, wc], -1))
    print('MAPS', json.dumps(report))
    Image.fromarray((np.concatenate([p if p.shape[0] == S2 else p for p in prev], 1) * 255).astype(np.uint8)).resize(
        (2 * 1024, 1024)).save(HERE / 'review' / 'regions_body.png')


if __name__ == '__main__':
    main()
