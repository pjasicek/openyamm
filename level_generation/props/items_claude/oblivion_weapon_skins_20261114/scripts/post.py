#!/usr/bin/env python3
"""Step 4 of the Oblivion weapon skins (README.md): Meshy's 4K paint -> the skin's maps, then the skin GLB.

  python3 post.py transfer <template>            maps of the template carried onto the new UVs (once per template):
                                                 work/<template>/maps/{metal_mask,old_color,position,normal}.npy/png
  python3 post.py coverage <template>            the cached island coverage (transfer writes it; layouts before)
  python3 post.py skin <template> <tier> <job>   work/<template>/t<tier>/{basecolor,normal,mr}.png and
                                                 work/<template>/t<tier>/<template>_t<tier>.glb; a job of another
                                                 tier recolours that paint (the low bow from the mid one)

skin, in order (TEXTURE_QUALITY_PASS.md section 0 step 6; the held-sword pilot's blade pass):
1. Meshy's maps 4K -> 2K once (Lanczos); its normal map is +y down (DirectX): flipped to glTF.
2. Gentle grade (claude_shared/grade_basecolor.py: fine 1.0, local 0.3, AO 0.5, contrast 1.06, saturation 1.15) on
   the AO bake (bake_ao.py).
3. Metal (the template's own specular mask carried onto the new UVs: Oblivion masks metal, not leather or wood):
   detail finer than sigma 3 texels kept at FINE_KEEP (Meshy paints a 4-8 texel weave on metal), albedo scaled to the
   tier's median linear luminance (Khronos metal range), metallic 0.85-1.0 with Meshy's variation.
4. Blades (sword metal past the guard): a honed edge band (brighter, glossier), a lengthwise grinding grain from the
   3D position (colour, roughness and a small normal tilt across the blade, seamless across UV pieces) and a slow
   polish variation along the length; roughness by tier.
5. MR: R = AO (openyamm_specular_occlusion: orm), G roughness, B metallic, at 1K; normal and colour 2K.
6. gutter_fill.py's nearest-texel fill last on every map; the GLB from the template (write_skin.py).
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
SHARED = os.path.join(REPO, 'level_generation', 'creatures', 'claude_shared')
sys.path.insert(0, HERE)
import glb_io
sys.path.insert(0, SHARED)
from gutter_fill import coverage, pad

SIZE = 2048
FINE_SIGMA = 4.5
# Per tier: median linear luminance of metal, roughness of blade flats (lo, hi), honed-edge roughness factor, fine
# detail kept on metal.
TIER = {1: {'metal_lum': 0.36, 'rough': (0.42, 0.75), 'edge': 0.55, 'fine': 0.12, 'rust': True},
        2: {'metal_lum': 0.52, 'rough': (0.24, 0.5), 'edge': 0.35, 'fine': 0.1, 'rust': False},
        3: {'metal_lum': 0.62, 'rough': (0.12, 0.32), 'edge': 0.35, 'fine': 0.1, 'rust': False},
        # Legendary: polished, more of the paint's fine detail kept (runes, damascus, filigree); metal luminance per
        # weapon (LEGENDARY_LUM: its dark or pale exotic metal).
        4: {'metal_lum': 0.5, 'rough': (0.1, 0.3), 'edge': 0.4, 'fine': 0.3, 'rust': False}}
# Tier 4 metal median luminance per weapon (codex_masters.py LEGENDARY): dark metals stay at or above 0.3 so they still
# read as polished metal in a dim dungeon.
LEGENDARY_LUM = {'w_longsword': 0.32, 'w_claymore': 0.34, 'w_mace': 0.3, 'w_bow': 0.62, 'w_shortsword': 0.6,
                 'w_dagger': 0.32, 'w_waraxe': 0.34, 'w_battleaxe': 0.62, 'w_warhammer': 0.34, 'w_staff': 0.6,
                 's_steelshield': 0.36}
# Metal luminance is brought to the tier's median by a power curve (contrast kept at CONTRAST of the paint's, so a
# dark paint lifted 5-9 times does not turn its mottling into blotches).
CONTRAST = 0.7
# Per template adjustments of the tier settings. The shield's broad engraved plates: more of the paint's detail (its
# paint has no weave), a darker metal and rougher flats (mirror plates reflected the dark ground and read black-olive).
# The bow (v2, README.md "Bow v2"): its gold filigree and fittings are the detail, not Meshy's weave, so most of it is
# kept (the v1 high bow's filigree went soft at 0.1).
TEMPLATE_CFG = {'s_steelshield': {'fine': 0.6, 'lum_scale': 0.8, 'rough_add': 0.32}, 'w_bow': {'fine': 0.85}}
# Metal colour saturation (linear, (max - min) / max) is capped at gold's (F0 1.0, 0.77, 0.34): Meshy's gold came back
# near (1, 0.66, 0.05) and drew olive-green in game.
METAL_SAT_MAX = 0.64
# A legendary paint's metal is lifted at most this much (Meshy paints dark exotic metal near black; lifted to the
# tier's median it turned white, the voidstone mace 2026-11-14).
LEGENDARY_MAX_GAIN = 3.0
# Legendary rune inlays (codex_masters.py LEGENDARY, "luminous enamel"): hue (degrees), hue tolerance, minimum
# saturation and value of the paint. They become non-metal enamel with an emission of their own colour (emissive.png,
# x RUNE_GLOW; write_skin.py adds it as the material's emissiveTexture). Weapons whose runes share their hue with the
# metal around them (bronze, gold) have none: their inlay stays paint.
# A list of entries is their union. STAR_RUNES: the v2 legendaries' cyan channels and violet-cyan crystals (README.md
# "Bow v2" and "Legendary v2": the bow, the claymore, the war axe, the warhammer, the staff and the shield).
STAR_RUNES = [(185, 28, 0.35, 0.5), (275, 32, 0.35, 0.45)]
RUNES = {'w_bow': STAR_RUNES, 'w_longsword': (205, 30, 0.3, 0.55), 'w_claymore': STAR_RUNES,
         'w_mace': (290, 35, 0.45, 0.45), 'w_shortsword': (130, 40, 0.4, 0.45), 'w_dagger': (0, 16, 0.6, 0.5),
         'w_battleaxe': (195, 25, 0.45, 0.6), 'w_staff': STAR_RUNES, 'w_waraxe': STAR_RUNES,
         'w_warhammer': STAR_RUNES, 's_steelshield': STAR_RUNES}
RUNE_GLOW = 0.7
# KHR_materials_emissive_strength per template (write_skin.py, from t<tier>/emissive.json): the legendary bow's rune
# channels must read as glowing in daylight (2026-11-14 review: the v1 legendary bow read plain).
EMISSIVE_STRENGTH = {'w_bow': 2.5, 'w_claymore': 2.5, 'w_waraxe': 2.5, 'w_warhammer': 2.5, 'w_staff': 2.5,
                     's_steelshield': 2.5}
# Templates whose Oblivion specular mask is high on wood too (the staff's glossy wood is all "metal" there): metal
# comes from the paint's colour instead, per tier: (hue, tolerance, min saturation, min value, max saturation) for
# gold and silver fittings; tiers without an entry have no metal.
# None for a tier: the specular mask as usual. The bow v2 (README.md "Bow v2"): the high bow's gold filigree runs over
# the limbs where Oblivion's mask has wood, and its black lacquer over the mask's metal tips; the legendary's
# platinum likewise.
METAL_BY_COLOUR = {'w_staff': {3: [(45, 18, 0.45, 0.55, 1.0)],
                               4: [(45, 18, 0.45, 0.55, 1.0), (0, 180, 0.0, 0.72, 0.14)]},
                   'w_bow': {1: None, 2: None, 3: [(45, 18, 0.45, 0.55, 1.0)],
                             4: [(45, 18, 0.45, 0.55, 1.0), (0, 180, 0.0, 0.66, 0.16)]}}
# Procedural rune channels and crystals (README.md "Legendary v2"), for legendaries whose Meshy paint dropped the
# masters' glowing channel (the staff v2 came back as dark blue noise without its channel or crystal): drawn from the
# texels' template positions, so they run clean and continuous across UV seams. helix: strands winding around the long
# axis (axis index into the position) between y_range with one turn per pitch units (0: straight along the axis),
# width in units, a diamond node every node units (the warhammer's and the war axe's plain platinum twisted shafts,
# which fill the idle frame, get three straight channels); crystals: (axis value, side) pairs, a faceted violet-cyan stone of radius units on the front (+z)
# or back (-z) of the part at that height.
CHANNELS = {'w_staff': {'helix': {'axis': 1, 'y_range': (-80.0, 9.0), 'pitch': 28.0, 'strands': 2, 'width': 0.34,
                                  'node': 3.2},
                        'crystals': {'at': [(13.0, 1), (13.0, -1)], 'radius': 1.5}},
            'w_warhammer': {'helix': {'axis': 1, 'y_range': (6.5, 20.8), 'pitch': 0.0, 'strands': 3, 'width': 0.26,
                                      'node': 2.4}},
            'w_waraxe': {'helix': {'axis': 1, 'y_range': (6.3, 18.3), 'pitch': 0.0, 'strands': 3, 'width': 0.26,
                                   'node': 2.4}}}
CHANNEL_CYAN = np.array([0.25, 0.92, 1.0])
CHANNEL_VIOLET = np.array([0.68, 0.32, 1.0])
# Pieced uploads (prep_pieced.py: the bow from v2 on) leave the string out: its texels keep the tier's earlier skin
# (work/<template>/t<tier>_v1/).
PIECED = {'w_bow': 2}
# The kept string recoloured for a new tier look (sRGB colour times the earlier string's relative brightness): the
# legendary bow's v1 string was bone-gold, now pale silver to go with its platinum.
STRING_COLOUR = {('w_bow', 4): (0.8, 0.83, 0.88)}
# Low tiers repainted from the mid tier's paint (post.py skin <template> 1 <template>_t2_v1): Meshy turns grey or dark
# plain wood on thin limbs and shafts into black-and-white noise (zebra, snakeskin, leopard; the bow three times, the
# staff once). Wood colour, worn-patch colour, and a cloth wrap found by its hue in the mid paint (hue, tolerance,
# new colour).
RECOLOUR = {('w_bow', 1): {'wood': (0.36, 0.25, 0.165), 'worn': (0.5, 0.42, 0.33)},
            ('w_staff', 1): {'wood': (0.32, 0.27, 0.21), 'worn': (0.5, 0.46, 0.4),
                             'wrap': (215, 40, (0.58, 0.52, 0.4))}}
# Templates with the same mesh as another (write_skin.py UV_FROM): written from its paint.
SAME_PAINT = {'w_staff': ('w_staff_grip',)}
BLADED = ('w_longsword', 'w_claymore', 'w_shortsword', 'w_dagger')


def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def value_noise(x, seed):
    i = np.floor(x).astype(np.int64)
    f = x - i

    def h(k):
        k = (k * 374761393 + seed * 668265263) & 0xFFFFFFFF
        k = ((k ^ (k >> 13)) * 1274126177) & 0xFFFFFFFF
        return (k & 0xFFFF) / 65535.0 * 2 - 1
    u = f * f * (3 - 2 * f)
    return h(i) * (1 - u) + h(i + 1) * u


def template(name):
    doc, binary = glb_io.read(os.path.join(REPO, 'assets_dev', 'engine', 'view_model', f'{name}.glb'))
    mesh, prim = glb_io.mesh_primitive(doc, 'Bow' if name == 'w_bow' else None)
    pos = glb_io.accessor(doc, binary, prim['attributes']['POSITION']).astype(np.float64)
    nrm = glb_io.accessor(doc, binary, prim['attributes']['NORMAL']).astype(np.float64)
    uv0 = glb_io.accessor(doc, binary, prim['attributes']['TEXCOORD_0']).astype(np.float64)
    tri = glb_io.accessor(doc, binary, prim['indices']).astype(np.int64).reshape(-1, 3)
    return doc, binary, prim, pos, nrm, uv0, tri


def material_image(doc, binary, material, role):
    m = doc['materials'][material]
    index = {'color': m['pbrMetallicRoughness']['baseColorTexture']['index'],
             'mr': m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],
             'normal': m['normalTexture']['index']}[role]
    image = doc['images'][doc['textures'][index]['source']]
    import io
    return Image.open(io.BytesIO(glb_io.view_bytes(doc, binary, image['bufferView'])))


def rasterize(uv, size):
    """Triangle id (-1 outside) and barycentrics per texel centre for UVs (F, 3, 2) in [0, 1], v down."""
    tid = np.full((size, size), -1, np.int64)
    bary = np.zeros((size, size, 3))
    q = uv * size
    for f, t in enumerate(q):
        x0, y0 = np.floor(t.min(0)).astype(int)
        x1, y1 = np.ceil(t.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        px, py = xs + 0.5, ys + 0.5
        (ax, ay), (bx, by), (cx, cy) = t
        det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(det) < 1e-12:
            continue
        l0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / det
        l1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / det
        l2 = 1 - l0 - l1
        inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        tid[ys[inside], xs[inside]] = f
        bary[ys[inside], xs[inside]] = np.stack([l0, l1, l2], -1)[inside]
    return tid, bary


def transfer(name):
    work = os.path.join(PROJECT, 'work', name)
    maps = os.path.join(work, 'maps')
    os.makedirs(maps, exist_ok=True)
    doc, binary, prim, pos, nrm, uv0, tri = template(name)
    uv = np.load(os.path.join(work, 'uv_template.npy'))
    tid, bary = rasterize(uv, SIZE)
    inside = tid >= 0
    t = np.where(inside, tid, 0)
    corners = tri[t]                                           # (H, W, 3)
    interp = lambda attr: np.einsum('hwc,hwck->hwk', bary, attr[corners])
    p = interp(pos)
    n = interp(nrm)
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
    ouv = interp(uv0)
    material = prim['material']
    spec = np.asarray(material_image(doc, binary, material, 'mr').convert('RGB'), np.float64) / 255.0
    color = np.asarray(material_image(doc, binary, material, 'color').convert('RGB'), np.float64) / 255.0

    def sample(img, coords):
        h, w = img.shape[:2]
        x = np.clip((coords[..., 0] % 1.0) * w, 0, w - 1).astype(int)
        y = np.clip((coords[..., 1] % 1.0) * h, 0, h - 1).astype(int)
        return img[y, x]
    mask = sample(spec, ouv)[..., 0]
    old = sample(color, ouv)
    mask[~inside] = 0
    old[~inside] = 0
    np.save(os.path.join(maps, 'tid.npy'), tid.astype(np.int32))
    np.save(os.path.join(maps, 'position.npy'), p.astype(np.float32))
    np.save(os.path.join(maps, 'normal.npy'), n.astype(np.float32))
    Image.fromarray((mask * 255).astype(np.uint8)).save(os.path.join(maps, 'spec_mask.png'))
    Image.fromarray((old * 255).astype(np.uint8)).save(os.path.join(maps, 'old_color.png'))
    np.savez(os.path.join(maps, 'uv_tris.npz'), uv=uv)
    for size in (SIZE, SIZE // 2):
        island_coverage(maps, size)
    print('TRANSFER', name, 'covered %.1f %%' % (inside.mean() * 100), 'spec p10/50/90',
          np.percentile(mask[inside], [10, 50, 90]).round(2))


def island_coverage(maps, size):
    """gutter_fill.coverage of the layout at size x size, cached in maps/coverage_<size>.npy."""
    path = os.path.join(maps, f'coverage_{size}.npy')
    if os.path.exists(path):
        return np.load(path)
    covered = coverage(np.load(os.path.join(maps, 'uv_tris.npz'))['uv'].astype(np.float64), size, size)
    np.save(path, covered)
    return covered


def rune_mask(colour, inside, hue, tolerance, min_sat, min_val):
    """Soft mask of the paint's luminous inlay colour (sRGB 0..1): hue within tolerance degrees, saturation and value
    above the minimums."""
    mx, mn = colour.max(-1), colour.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    r, g, b = colour[..., 0], colour[..., 1], colour[..., 2]
    h = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    dh = np.abs((h - hue + 180) % 360 - 180)
    mask = (1 - smoothstep(tolerance * 0.7, tolerance, dh)) * smoothstep(min_sat - 0.08, min_sat + 0.08, sat) * \
        smoothstep(min_val - 0.08, min_val + 0.08, mx)
    return soft_mask(np.where(inside, mask, 0.0), inside, 0.6)


def soft_mask(mask, inside, sigma=0.8):
    """The mask blurred by sigma texels within the islands only (normalised convolution), zero outside."""
    from scipy import ndimage
    weight = ndimage.gaussian_filter(inside.astype(np.float64), sigma)
    blurred = ndimage.gaussian_filter(np.where(inside, mask, 0.0), sigma) / np.maximum(weight, 1e-6)
    return np.where(inside, np.clip(blurred, 0, 1), 0.0)


def string_texels(name, tid):
    """Texels of the bow's string: its own linked part of the template (under 100 triangles, under half a unit
    across in x; prep_pieced.py leaves the same part out of the upload)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    _, _, _, pos, _, _, tri = template(name)
    weld = np.unique(np.round(pos, 4), axis=0, return_inverse=True)[1].ravel()
    t = weld[tri]
    rows, cols = np.r_[t[:, 0], t[:, 1], t[:, 2]], np.r_[t[:, 1], t[:, 2], t[:, 0]]
    n = weld.max() + 1
    _, label = connected_components(coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)), directed=False)
    face_label = label[t[:, 0]]
    string = np.zeros(len(tri), bool)
    for part in np.unique(face_label):
        faces = face_label == part
        xs = pos[tri[faces]][..., 0]
        if faces.sum() < 100 and np.ptp(xs) < 0.5:
            string |= faces
    return (tid >= 0) & string[np.where(tid >= 0, tid, 0)]


def procedural_channels(name, p, inside):
    """CHANNELS: (mask 0..1, sRGB colour) per texel of the template's procedural rune channels and crystals."""
    cfg = CHANNELS[name]
    mask = np.zeros(inside.shape)
    colour = np.zeros(inside.shape + (3,))
    helix = cfg.get('helix')
    if helix:
        ax = helix['axis']
        a, b = [i for i in range(3) if i != ax]
        y = p[..., ax]
        lo, hi = helix['y_range']
        # The shaft's centre per height (it twists and leans): slice means, smoothed over +-4 units.
        bins = np.arange(lo - 6.0, hi + 7.0, 1.0)
        ys, ca, cb = [], [], []
        q = p[inside]
        for y0 in bins:
            sel = np.abs(q[:, ax] - y0) < 4.0
            if sel.sum() > 50:
                ys.append(y0)
                ca.append(q[sel, a].mean())
                cb.append(q[sel, b].mean())
        cy_a, cy_b = np.interp(y, ys, ca), np.interp(y, ys, cb)
        da, db = p[..., a] - cy_a, p[..., b] - cy_b
        r = np.hypot(da, db)
        theta = np.arctan2(db, da)
        half = np.zeros(inside.shape) + helix['width'] / 2
        phase = (y / helix['node']) % 1.0 - 0.5
        half *= 1.0 + 1.6 * np.clip(1.0 - np.abs(phase) * helix['node'] / 0.55, 0.0, 1.0)
        best = np.full(inside.shape, np.inf)
        for k in range(helix['strands']):
            turn = 2 * np.pi * ((y / helix['pitch'] if helix['pitch'] else 0.0) + k / helix['strands'])
            d = (theta - turn + np.pi) % (2 * np.pi) - np.pi
            best = np.minimum(best, np.abs(d) * np.maximum(r, 0.2))
        line = 1.0 - smoothstep(half * 0.75, half, best)
        line *= smoothstep(lo, lo + 2.0, y) * (1.0 - smoothstep(hi - 2.0, hi, y))
        t = np.clip((y - lo) / (hi - lo), 0, 1)
        ends = smoothstep(0.55, 1.0, np.abs(2 * t - 1))[..., None]
        line_colour = CHANNEL_CYAN * (1 - ends) + CHANNEL_VIOLET * ends
        mask = np.maximum(mask, np.where(inside, line, 0.0))
        colour = np.where(line[..., None] > 0, line_colour, colour)
    crystals = cfg.get('crystals')
    if crystals:
        q = p[inside]
        for height, side in crystals['at']:
            sel = np.abs(q[:, 1] - height) < 1.5
            centre_xz = np.median(q[sel][:, [0, 2]], axis=0)
            near = sel & (np.abs(q[:, 0] - centre_xz[0]) < 1.5)
            tip = q[near][np.argmax(side * q[near][:, 2])]
            d = p - tip
            dist = np.linalg.norm(d, axis=-1)
            stone = (1.0 - smoothstep(crystals['radius'] * 0.85, crystals['radius'], dist)) * (side * d[..., 2] > -1.2)
            # Facets: six sectors around the stone's centre, and a violet core inside a cyan rim.
            angle = np.arctan2(d[..., 1], d[..., 0])
            facet = 0.78 + 0.22 * np.cos(6 * angle + 0.4) * np.cos(3 * angle)
            core = smoothstep(crystals['radius'] * 0.2, crystals['radius'] * 0.9, dist)[..., None]
            stone_colour = (CHANNEL_VIOLET * (1 - core) + CHANNEL_CYAN * core) * facet[..., None]
            stone = np.where(inside, stone, 0.0)
            colour = np.where(stone[..., None] > mask[..., None], stone_colour, colour)
            mask = np.maximum(mask, stone)
    return mask, np.clip(colour, 0, 1)


def blade_frame(name, pos):
    """Guard height (widest slice across x) and, along y, the blade's centre and half width past it."""
    lo, hi = pos[:, 1].min(), pos[:, 1].max()
    bins = np.linspace(lo, hi, 61)
    widths = []
    for a, b in zip(bins[:-1], bins[1:]):
        sel = (pos[:, 1] >= a) & (pos[:, 1] <= b)
        widths.append(np.ptp(pos[sel, 0]) if sel.sum() > 2 else 0)
    g = int(np.argmax(widths))
    guard_top = bins[g + 1]
    return guard_top, hi


def skin(name, tier, job):
    tier = int(tier)
    cfg = dict(TIER[tier])
    if tier == 4:
        cfg['metal_lum'] = LEGENDARY_LUM[name]
    extra = TEMPLATE_CFG.get(name, {})
    cfg['fine'] = max(cfg['fine'], extra.get('fine', 0.0))
    cfg['metal_lum'] *= extra.get('lum_scale', 1.0)
    cfg['rough'] = tuple(r + extra.get('rough_add', 0.0) for r in cfg['rough'])
    work = os.path.join(PROJECT, 'work', name)
    maps = os.path.join(work, 'maps')
    out = os.path.join(work, f't{tier}')
    os.makedirs(out, exist_ok=True)
    src = os.path.join(PROJECT, 'meshy', job)
    # 1. One downsample.
    loaded = {}
    for role in ('base_color', 'metallic', 'roughness', 'normal'):
        image = Image.open(os.path.join(src, f'texture_urls_0_{role}.png'))
        image = image.convert('RGB') if role in ('base_color', 'normal') else image.convert('L')
        loaded[role] = image.resize((SIZE, SIZE), Image.LANCZOS)
    loaded['base_color'].save(os.path.join(out, 'base_color_2k.png'))
    # 2. Gentle grade on the AO bake.
    subprocess.run([sys.executable, os.path.join(SHARED, 'grade_basecolor.py'), os.path.join(out, 'base_color_2k.png'),
                    '--ao', os.path.join(maps, 'ao.png'), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5',
                    '--contrast', '1.06', '--saturation', '1.15'], check=True, stdout=subprocess.DEVNULL)
    colour = np.asarray(Image.open(os.path.join(out, 'base_color_2k_graded.png')).convert('RGB'), np.float64) / 255
    recolour = not job.startswith(f'{name}_t{tier}_')
    meshy_n = np.asarray(loaded['normal'], np.float64) / 127.5 - 1.0
    meshy_n[..., 1] *= -1.0                                       # DirectX -> glTF
    mm = np.asarray(loaded['metallic'], np.float64) / 255
    rr = np.asarray(loaded['roughness'], np.float64) / 255
    ao = np.asarray(Image.open(os.path.join(maps, 'ao.png')).convert('L'), np.float64) / 255
    tid = np.load(os.path.join(maps, 'tid.npy'))
    inside = tid >= 0
    p = np.load(os.path.join(maps, 'position.npy')).astype(np.float64)
    n = np.load(os.path.join(maps, 'normal.npy')).astype(np.float64)
    spec = np.asarray(Image.open(os.path.join(maps, 'spec_mask.png')), np.float64) / 255
    # Oblivion's specular mask is a flat 0.15 on leather and wood and higher on metal. Blurred within the islands
    # only (normalised): blurred against the empty gutter, island borders fell to about 65 % metallic and their lifted
    # metal albedo drew as thin white diffuse lines across every seam (the claymore's quillons, 2026-11-14).
    metal = soft_mask(np.clip((spec - 0.16) / 0.05, 0, 1), inside)
    if name == 'w_bow':
        # Oblivion's bow wood is glossy, so its specular mask is high there too: the wood (red-brown in the
        # template's colour) is taken out; the grey fittings stay metal.
        old = np.asarray(Image.open(os.path.join(maps, 'old_color.png')).convert('RGB'), np.float64) / 255
        wood = np.clip((old[..., 0] - old[..., 2] - 0.03) / 0.05, 0, 1)
        wood = soft_mask(wood, inside)
        metal = metal * (1 - wood)
    if name in METAL_BY_COLOUR and METAL_BY_COLOUR[name].get(tier, []) is not None:
        metal = np.zeros(inside.shape)
        for hue, tolerance, min_sat, min_val, max_sat in METAL_BY_COLOUR[name].get(tier, []):
            found = rune_mask(colour, inside, hue, tolerance, min_sat, min_val)
            mx, mn = colour.max(-1), colour.min(-1)
            found *= 1 - smoothstep(max_sat, max_sat + 0.06, (mx - mn) / np.maximum(mx, 1e-4))
            metal = np.maximum(metal, found)
    metal[~inside] = 0
    runes = np.zeros(inside.shape)
    if tier == 4 and name in RUNES:
        entries = RUNES[name] if isinstance(RUNES[name], list) else [RUNES[name]]
        runes = np.max([rune_mask(colour, inside, *entry) for entry in entries], axis=0)
        metal = metal * (1 - runes)
    metal_t = metal > 0.5
    if recolour:
        # A tier painted from another tier's paint: the low bow from the mid bow's clean yew (2026-11-14). Meshy painted
        # the low bow's grey ash (v1, a zebra weave), its retry (v2, snakeskin) and plain dark elm (v3, leopard spots)
        # with noise on the thin limbs every time. The yew's grain is kept as structure under a dark, weathered elm
        # brown with slow grime and lighter worn patches from the 3D position; the fittings go blackened iron.
        lum = colour @ np.array([0.299, 0.587, 0.114])
        wood_t = inside & ~metal_t
        mean, spread = np.median(lum[wood_t]), max(np.std(lum[wood_t]), 1e-3)
        grain = np.clip((lum - mean) / spread, -2.5, 2.5)
        along = p[..., 1] + 0.37 * p[..., 0] + 0.21 * p[..., 2]
        grime = value_noise(along / 7.0, 11) * 0.6 + value_noise(along / 2.3 + 0.5 * p[..., 0], 12) * 0.4
        worn = smoothstep(0.45, 0.8, value_noise(along / 4.0 + 1.7 * p[..., 2], 13))
        look = RECOLOUR[(name, tier)]
        elm = np.array(look['wood']) * (1 + 0.28 * grain[..., None]) * (1 + 0.3 * grime[..., None])
        elm = elm * (1 - 0.35 * worn[..., None]) + np.array(look['worn']) * 0.35 * worn[..., None]
        if 'wrap' in look:
            hue, tolerance, cloth = look['wrap']
            wrap = rune_mask(colour, inside, hue, tolerance, 0.25, 0.15)
            hemp = np.array(cloth) * (1 + 0.35 * grain[..., None])
            elm = elm * (1 - wrap[..., None]) + hemp * wrap[..., None]
        iron = np.clip(lum[..., None] * np.array([0.62, 0.62, 0.66]), 0, 1)
        colour = np.clip(np.where(metal_t[..., None], iron, elm), 0, 1)
        rr = np.clip(0.62 + 0.18 * rr + 0.06 * grime, 0, 1)

    # 3. Weave filter and albedo on metal.
    blur = np.asarray(Image.fromarray((colour * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(FINE_SIGMA)),
                      np.float64) / 255
    keep = np.maximum(1 - metal + metal * cfg['fine'], runes)[..., None]
    colour = blur + (colour - blur) * keep
    lin = srgb_to_linear(colour)
    lum = lin @ np.array([0.2126, 0.7152, 0.0722])
    median = max(np.median(lum[metal_t]), 1e-3) if metal_t.any() else 1.0
    if tier == 4:
        cfg['metal_lum'] = min(cfg['metal_lum'], median * LEGENDARY_MAX_GAIN)
    gain = cfg['metal_lum'] / median
    # Tier 1: rust (red-orange, saturated) on metal is not metal: it keeps its paint and turns rough.
    rust = np.zeros(inside.shape)
    if cfg['rust']:
        mx, mn = colour.max(-1), colour.min(-1)
        sat = (mx - mn) / np.maximum(mx, 1e-3)
        hue_red = (colour[..., 0] >= colour[..., 1]) & (colour[..., 1] >= colour[..., 2]) & (
            (colour[..., 1] - colour[..., 2]) < 0.75 * (colour[..., 0] - colour[..., 2]))
        rust = np.where(metal_t & hue_red, smoothstep(0.25, 0.45, sat), 0.0)
    target = cfg['metal_lum'] * (np.maximum(lum, 1e-4) / median) ** CONTRAST
    lifted = np.minimum(lin * (target / np.maximum(lum, 1e-4))[..., None], 0.95)
    mx = lifted.max(-1, keepdims=True)
    sat = (mx - lifted.min(-1, keepdims=True)) / np.maximum(mx, 1e-4)
    lifted = mx - (mx - lifted) * np.minimum(1.0, METAL_SAT_MAX / np.maximum(sat, 1e-4))
    m3 = (metal * (1 - rust))[..., None]
    lin = lin * (1 - m3) + lifted * m3

    # 4. Blades.
    _, _, _, tpos, _, _, _ = template(name)
    rough = rr.copy()
    lo_r, hi_r = np.percentile(rr[metal_t], [5, 95]) if metal_t.any() else (0.0, 1.0)
    r_metal = cfg['rough'][0] + (cfg['rough'][1] - cfg['rough'][0]) * np.clip((rr - lo_r) / max(hi_r - lo_r, 1e-3),
                                                                              0, 1)
    tilt_n = np.zeros_like(n)
    blade = np.zeros(inside.shape, bool)
    edge = np.zeros(inside.shape)
    if name in BLADED:
        guard_top, tip = blade_frame(name, tpos)
        L = tip - guard_top
        along = (p[..., 1] - guard_top) / L
        blade = inside & metal_t & (along > 0.02)
        # Half width per height from the mesh's outline.
        # Exact for the polygon: where the mesh edges cross each height (the blade is a few long triangles).
        _, _, _, _, _, _, ttri = template(name)
        edges = np.unique(np.sort(np.concatenate([ttri[:, [0, 1]], ttri[:, [1, 2]], ttri[:, [2, 0]]]), 1), axis=0)
        pa, pb = tpos[edges[:, 0]], tpos[edges[:, 1]]
        ys = np.linspace(guard_top, tip - 1e-3, 200)
        half = np.full(len(ys), np.nan)
        for i, y in enumerate(ys):
            cross = (np.minimum(pa[:, 1], pb[:, 1]) <= y) & (np.maximum(pa[:, 1], pb[:, 1]) >= y) & (
                np.abs(pa[:, 1] - pb[:, 1]) > 1e-9)
            if cross.any():
                t = (y - pa[cross, 1]) / (pb[cross, 1] - pa[cross, 1])
                half[i] = np.abs(pa[cross, 0] + t * (pb[cross, 0] - pa[cross, 0])).max()
        ok = np.isfinite(half)
        hw = np.interp(p[..., 1], ys[ok], half[ok])
        across = np.abs(p[..., 0]) / np.maximum(hw, 1e-6)
        edge = np.where(blade, smoothstep(0.78, 0.86, across), 0.0)
        # Grinding grain: fine streaks across the blade (about 0.25 units), wandering slowly along it.
        coord = p[..., 0] / 0.25 + value_noise(p[..., 1] / 3.0, 3) * 2.0
        grain = 0.6 * value_noise(coord, 1) + 0.4 * value_noise(coord * 2.3, 2)
        grain = np.where(blade, grain, 0.0)
        # Slow polish variation along the blade (smudges, wipe marks).
        slow = np.where(blade, value_noise(p[..., 1] / 6.0 + 0.3 * p[..., 0], 7), 0.0)
        r_metal = r_metal * (1 - (1 - cfg['edge']) * edge) + 0.05 * grain + 0.1 * slow
        lin = lin * (1 + (0.4 * edge + 0.08 * grain + 0.08 * slow)[..., None])
        # Grain as a small tilt across the blade (x), from its slope.
        slope = (value_noise(coord + 0.05, 1) - value_noise(coord - 0.05, 1)) * 6.0
        tilt_n[..., 0] = np.where(blade, slope * 0.08, 0.0)
    rough = np.where(metal_t, r_metal, rough)
    rough = rough * (1 - rust) + 0.85 * rust
    rough = rough * (1 - runes) + 0.4 * runes
    metal = metal * (1 - 0.8 * rust)
    metallic = metal * (0.85 + 0.15 * mm) + (1 - metal) * 0.05 * mm

    if tier == 4 and name in CHANNELS:
        chan, chan_colour = procedural_channels(name, p, inside)
        c3 = chan[..., None]
        lin = lin * (1 - c3) + srgb_to_linear(chan_colour) * c3
        runes = np.maximum(runes, chan)
        rough = rough * (1 - chan) + 0.3 * chan
        metallic = metallic * (1 - chan)

    # Normal: Meshy's detail (glTF convention) and the grain tilt, expressed in each texel's tangent frame.
    normal = meshy_n.copy()
    if name in BLADED:
        uv = np.load(os.path.join(maps, 'uv_tris.npz'))['uv'] * SIZE
        doc, binary, prim, tp, tn, tuv, tt = template(name)
        f = np.where(inside, tid, 0)
        p0, p1, p2 = tp[tt[:, 0]], tp[tt[:, 1]], tp[tt[:, 2]]
        q0, q1, q2 = uv[:, 0], uv[:, 1], uv[:, 2]
        du1, du2 = q1 - q0, q2 - q0
        det = du1[:, 0] * du2[:, 1] - du1[:, 1] * du2[:, 0]
        det = np.where(np.abs(det) < 1e-12, 1e-12, det)
        e1, e2 = p1 - p0, p2 - p0
        dpdx = (e1 * du2[:, 1:2] - e2 * du1[:, 1:2]) / det[:, None]     # along +columns (u)
        dpdy = -(e2 * du1[:, 0:1] - e1 * du2[:, 0:1]) / det[:, None]    # up the image (glTF +y)
        tx, ty = dpdx[f], dpdy[f]
        tx = tx - n * np.sum(tx * n, -1, keepdims=True)
        tx /= np.maximum(np.linalg.norm(tx, axis=-1, keepdims=True), 1e-12)
        ty = ty - n * np.sum(ty * n, -1, keepdims=True) - tx * np.sum(ty * tx, -1, keepdims=True)
        ty /= np.maximum(np.linalg.norm(ty, axis=-1, keepdims=True), 1e-12)
        world = n + tilt_n
        world /= np.maximum(np.linalg.norm(world, axis=-1, keepdims=True), 1e-9)
        ts = np.stack([np.sum(world * tx, -1), np.sum(world * ty, -1), np.sum(world * n, -1)], -1)
        # Meshy's normal detail on the blade is mostly its weave: kept at 15 %.
        soft = meshy_n * np.array([0.15, 0.15, 1.0])
        soft /= np.maximum(np.linalg.norm(soft, axis=-1, keepdims=True), 1e-9)
        blend = np.stack([soft[..., 0] + ts[..., 0], soft[..., 1] + ts[..., 1], soft[..., 2] * ts[..., 2]], -1)
        blend /= np.maximum(np.linalg.norm(blend, axis=-1, keepdims=True), 1e-9)
        normal = np.where(blade[..., None], blend, meshy_n)
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-9)

    # 5. Maps.
    Image.fromarray((linear_to_srgb(lin) * 255 + 0.5).astype(np.uint8)).save(os.path.join(out, 'basecolor.png'))
    emissive_path = os.path.join(out, 'emissive.png')
    if runes.any():
        glow = linear_to_srgb(np.clip(lin * (runes * RUNE_GLOW / 0.5)[..., None], 0, 1))
        Image.fromarray((pad(glow, inside) * 255 + 0.5).astype(np.uint8)).resize((SIZE // 2, SIZE // 2),
                                                                                  Image.LANCZOS).save(emissive_path)
    elif os.path.exists(emissive_path):
        os.remove(emissive_path)
    strength_path = os.path.join(out, 'emissive.json')
    if runes.any() and name in EMISSIVE_STRENGTH:
        json.dump({'strength': EMISSIVE_STRENGTH[name]}, open(strength_path, 'w'))
    elif os.path.exists(strength_path):
        os.remove(strength_path)
    Image.fromarray(np.clip((normal + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(out, 'normal.png'))
    mr = np.stack([np.clip(0.35 + 0.65 * ao, 0, 1), np.clip(rough, 0.05, 1), np.clip(metallic, 0, 1)], -1)
    # Padded from the islands before the 1K downsample, so border texels do not average with the empty gutter.
    mr = pad(mr, inside)
    Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).resize((SIZE // 2, SIZE // 2), Image.LANCZOS).save(
        os.path.join(out, 'mr.png'))
    # The string of a pieced upload (not in it): the tier's earlier skin.
    version = int(job.rsplit('_v', 1)[1]) if '_v' in job else 1
    if name in PIECED and version >= PIECED[name] and not recolour:
        keep = string_texels(name, tid)
        earlier = os.path.join(work, f't{tier}_v1')
        for file in ('basecolor.png', 'normal.png', 'mr.png', 'emissive.png'):
            path = os.path.join(out, file)
            if not os.path.exists(path):
                continue
            image = Image.open(path)
            array = np.asarray(image).copy()
            mask = keep if array.shape[0] == SIZE else keep.reshape(SIZE // 2, 2, SIZE // 2, 2).any((1, 3))
            source = os.path.join(earlier, file)
            if os.path.exists(source):
                old = np.asarray(Image.open(source).convert(image.mode))
                array[mask] = old[mask]
                if file == 'basecolor.png' and (name, tier) in STRING_COLOUR:
                    lum = old[mask].astype(np.float64).mean(-1)
                    rel = lum / max(np.median(lum), 1.0)
                    array[mask] = np.clip(rel[:, None] * np.array(STRING_COLOUR[(name, tier)]) * 255, 0, 255)
            else:
                array[mask] = 0
            Image.fromarray(array, image.mode).save(path)
    # 6. Gutters last, then the GLB.
    # (gutter_fill.py's coverage and pad, the coverage cached per template and size: the swords' long blade slivers
    # make it take minutes.)
    for file in ('basecolor.png', 'normal.png', 'mr.png'):
        image = Image.open(os.path.join(out, file))
        array = np.asarray(image)
        Image.fromarray(pad(array, island_coverage(maps, array.shape[0])), image.mode).save(os.path.join(out, file))
    glb = os.path.join(out, f'{name}_t{tier}.glb')
    subprocess.run([sys.executable, os.path.join(HERE, 'write_skin.py'), name, str(tier), out, glb], check=True)
    for twin in SAME_PAINT.get(name, ()):
        subprocess.run([sys.executable, os.path.join(HERE, 'write_skin.py'), twin, str(tier), out,
                        os.path.join(out, f'{twin}_t{tier}.glb')], check=True)
    stats = {'metal_share': round(float(metal_t[inside].mean()), 3), 'metal_gain': round(float(gain), 2),
             'rust_share': round(float((rust > 0.5)[inside].mean()), 3),
             'blade_texels': int(blade.sum()), 'rune_share': round(float((runes > 0.5)[inside].mean()), 4),
             'rough_metal_p10_p50_p90': np.percentile(rough[metal_t], [10, 50, 90]).round(2).tolist()
             if metal_t.any() else None,
             'rough_blade_edge_vs_flat': [round(float(rough[blade & (edge > 0.9)].mean()), 2) if blade.any() else None,
                                          round(float(rough[blade & (edge < 0.1)].mean()), 2) if blade.any() else None]}
    json.dump(stats, open(os.path.join(out, 'post.json'), 'w'), indent=1)
    print('SKIN', name, tier, json.dumps(stats))


if __name__ == '__main__':
    if sys.argv[1] == 'transfer':
        transfer(sys.argv[2])
    elif sys.argv[1] == 'coverage':
        for size in (SIZE, SIZE // 2):
            island_coverage(os.path.join(PROJECT, 'work', sys.argv[2], 'maps'), size)
    else:
        skin(sys.argv[2], sys.argv[3], sys.argv[4])
