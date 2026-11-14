#!/usr/bin/env python3
"""Step 6 (README.md): Meshy's 4K paint -> one tier skin of a weapon kind.

  python3 -I post.py maps <kind>               work/<kind>/maps/{tid,bary}.npy and region.png from mesh.npz (once)
  python3 -I post.py skin <kind> <tier> <job>  work/<kind>/t<tier>/{basecolor,normal,mr[,emissive]}.png and
                                               work/<kind>/t<tier>/w_<kind>_t<tier>.glb; a job of another tier is
                                               recoloured to the low look (a refused low tier)

skin, in order (TEXTURE_QUALITY_PASS.md section 0 step 6; the Oblivion skins' post.py, regions from build.py's face
attribute instead of Oblivion's specular mask):
1. Meshy's maps 4K -> 2K once (Lanczos); its normal map is +y down (DirectX): flipped to glTF.
2. Gentle grade (claude_shared/grade_basecolor.py: fine 1.0, local 0.3, AO 0.5, contrast 1.06, saturation 1.15).
3. Metal (regions blade, edge, metal, brass): detail finer than sigma 4.5 texels kept at the tier's `fine` (Meshy's
   weave), steel albedo brought to the tier's median linear luminance by a power curve (70 % contrast kept), brass and
   gold keep their paint; tier-1 rust stays non-metal and rough.
4. Blades (regions blade and edge): the honed bevels (region edge) brighter and glossier, a lengthwise grinding grain
   from the 3D position (colour, roughness, a small normal tilt), a slow polish variation; roughness by tier.
5. Glow: the legendary tier's luminous inlays (bright cyan-blue paint on metal) become emissive and non-metal; gems and
   crystals glow by tier; a blaster's energy cell (region glow) always.
6. MR: R = AO (openyamm_specular_occlusion: orm), G roughness, B metallic, 1K; colour, normal, emissive 2K;
   gutter_fill.py last on every map, then the GLB (one mesh, one material, node w_<kind>).
"""
import io
import json
import os
import struct
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
SHARED = os.path.join(REPO, 'level_generation', 'creatures', 'claude_shared')

SIZE = 2048
FINE_SIGMA = 4.5
CONTRAST = 0.7
R = {'blade': 0, 'metal': 1, 'wood': 2, 'leather': 3, 'gem': 4, 'glow': 5, 'string': 6, 'dark': 7, 'brass': 8,
     'edge': 9}
METAL = (R['blade'], R['metal'], R['brass'], R['edge'])
STEEL = (R['blade'], R['metal'], R['edge'])
BLADE = (R['blade'], R['edge'])
# Per tier: steel's median linear luminance, blade-flat roughness (lo, hi), honed-edge roughness factor, fine detail
# kept on metal, rust, gem glow.
TIER = {1: {'metal_lum': 0.34, 'rough': (0.45, 0.78), 'edge': 0.55, 'fine': 0.12, 'rust': True, 'gem_glow': 0.0},
        2: {'metal_lum': 0.52, 'rough': (0.26, 0.52), 'edge': 0.35, 'fine': 0.1, 'rust': False, 'gem_glow': 0.15},
        3: {'metal_lum': 0.62, 'rough': (0.14, 0.34), 'edge': 0.35, 'fine': 0.1, 'rust': False, 'gem_glow': 0.25},
        4: {'metal_lum': 0.16, 'rough': (0.2, 0.42), 'edge': 0.4, 'fine': 0.12, 'rust': False, 'gem_glow': 0.55}}
# The wand's crystal glows on every tier (README.md "Wand glow", after the user's review): peak emission by tier, in the
# crystal's own hue (saturated, never white), brighter toward the tip and on the paint's light facets; it replaces the
# generic gem glow for the wand. (z0, z1): the crystal's height (glTF Y).
WAND_GLOW = {'tiers': {1: 0.2, 2: 0.45, 3: 0.55, 4: 1.0}, 'span': (17.6, 25.0)}


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


def maps(kind):
    work = os.path.join(PROJECT, 'work', kind, 'maps')
    mesh = np.load(os.path.join(work, 'mesh.npz'))
    tid, bary = rasterize(mesh['uv'], SIZE)
    np.save(os.path.join(work, 'tid.npy'), tid.astype(np.int32))
    np.save(os.path.join(work, 'bary.npy'), bary.astype(np.float32))
    inside = tid >= 0
    region = np.where(inside, mesh['region'][np.where(inside, tid, 0)], 255).astype(np.uint8)
    Image.fromarray(region).save(os.path.join(work, 'region.png'))
    print('MAPS', kind, 'covered %.1f %%' % (inside.mean() * 100),
          {k: round(float((region == v).mean() * 100), 1) for k, v in R.items() if (region == v).any()})


def tangent_frames(mesh, tid, inside, n):
    """Per texel, the surface directions of +u (columns) and of up the image (glTF +y of the normal map)."""
    uv = mesh['uv'] * SIZE
    p = mesh['pos']
    f = np.where(inside, tid, 0)
    q0, q1, q2 = uv[:, 0], uv[:, 1], uv[:, 2]
    du1, du2 = q1 - q0, q2 - q0
    det = du1[:, 0] * du2[:, 1] - du1[:, 1] * du2[:, 0]
    det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    e1, e2 = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]
    dpdx = (e1 * du2[:, 1:2] - e2 * du1[:, 1:2]) / det[:, None]
    dpdy = -(e2 * du1[:, 0:1] - e1 * du2[:, 0:1]) / det[:, None]
    tx, ty = dpdx[f], dpdy[f]
    tx = tx - n * np.sum(tx * n, -1, keepdims=True)
    tx /= np.maximum(np.linalg.norm(tx, axis=-1, keepdims=True), 1e-12)
    ty = ty - n * np.sum(ty * n, -1, keepdims=True) - tx * np.sum(ty * tx, -1, keepdims=True)
    ty /= np.maximum(np.linalg.norm(ty, axis=-1, keepdims=True), 1e-12)
    return tx, ty


def png_bytes(path):
    with open(path, 'rb') as handle:
        return handle.read()


def write_glb(path, kind, tier, mesh, images, emissive_strength=None):
    """One mesh, one material: corners deduplicated by position, normal and UV."""
    pos = mesh['pos'].reshape(-1, 3).astype(np.float32)
    nrm = mesh['nrm'].reshape(-1, 3)
    nrm = (nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)).astype(np.float32)
    uv = mesh['uv'].reshape(-1, 2).astype(np.float32)
    key = np.round(np.c_[pos, nrm * 1000, uv * 100000], 3)
    _, first, inverse = np.unique(key, axis=0, return_index=True, return_inverse=True)
    pos, nrm, uv = pos[first], nrm[first], uv[first]
    index = inverse.ravel().astype(np.uint32)
    views, accessors = [], []

    def add(data, target, component, kind_, count, minmax=False):
        views.append({'data': data.tobytes(), 'target': target})
        a = {'bufferView': len(views) - 1, 'componentType': component, 'count': count, 'type': kind_}
        if minmax:
            a['min'] = data.min(0).tolist()
            a['max'] = data.max(0).tolist()
        accessors.append(a)
        return len(accessors) - 1
    a_pos = add(pos, 34962, 5126, 'VEC3', len(pos), True)
    a_nrm = add(nrm, 34962, 5126, 'VEC3', len(nrm))
    a_uv = add(uv, 34962, 5126, 'VEC2', len(uv))
    a_idx = add(index, 34963, 5125, 'SCALAR', len(index))
    image_entries, textures = [], {}
    for role, file in images.items():
        views.append({'data': png_bytes(file), 'target': None})
        image_entries.append({'bufferView': len(views) - 1, 'mimeType': 'image/png'})
        textures[role] = len(image_entries) - 1
    material = {'name': f'w_{kind}_t{tier}', 'doubleSided': False,
                'pbrMetallicRoughness': {'metallicFactor': 1.0, 'roughnessFactor': 1.0,
                                         'baseColorTexture': {'index': textures['basecolor']},
                                         'metallicRoughnessTexture': {'index': textures['mr']}},
                'normalTexture': {'index': textures['normal']},
                'extras': {'openyamm_specular_occlusion': 'orm'}}
    if 'emissive' in textures:
        material['emissiveTexture'] = {'index': textures['emissive']}
        material['emissiveFactor'] = [1.0, 1.0, 1.0]
        if emissive_strength:
            material['extensions'] = {'KHR_materials_emissive_strength': {'emissiveStrength': emissive_strength}}
    doc = {'asset': {'version': '2.0', 'generator': 'view_model_weapons_20261114 post.py'},
           'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'name': f'w_{kind}', 'mesh': 0}],
           'meshes': [{'name': f'w_{kind}', 'primitives': [{'attributes': {'POSITION': a_pos, 'NORMAL': a_nrm,
                                                                           'TEXCOORD_0': a_uv},
                                                            'indices': a_idx, 'material': 0}]}],
           'materials': [material], 'samplers': [{}],
           'textures': [{'source': i, 'sampler': 0} for i in range(len(image_entries))],
           'images': image_entries, 'accessors': accessors, 'bufferViews': []}
    if 'extensions' in material:
        doc['extensionsUsed'] = ['KHR_materials_emissive_strength']
    blob = bytearray()
    for v in views:
        while len(blob) % 4:
            blob.append(0)
        entry = {'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(v['data'])}
        if v['target']:
            entry['target'] = v['target']
        doc['bufferViews'].append(entry)
        blob += v['data']
    while len(blob) % 4:
        blob.append(0)
    doc['buffers'] = [{'byteLength': len(blob)}]
    text = json.dumps(doc, separators=(',', ':')).encode()
    while len(text) % 4:
        text += b' '
    with open(path, 'wb') as handle:
        handle.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(text) + 8 + len(blob)))
        handle.write(struct.pack('<II', len(text), 0x4E4F534A) + text)
        handle.write(struct.pack('<II', len(blob), 0x004E4942) + bytes(blob))
    return len(index) // 3, len(pos)


def skin(kind, tier, job):
    tier = int(tier)
    cfg = TIER[tier]
    work = os.path.join(PROJECT, 'work', kind)
    mdir = os.path.join(work, 'maps')
    out = os.path.join(work, f't{tier}')
    os.makedirs(out, exist_ok=True)
    src = os.path.join(PROJECT, 'meshy', job)
    mesh = np.load(os.path.join(mdir, 'mesh.npz'))
    tid = np.load(os.path.join(mdir, 'tid.npy'))
    bary = np.load(os.path.join(mdir, 'bary.npy')).astype(np.float64)
    inside = tid >= 0
    t = np.where(inside, tid, 0)
    p = np.einsum('hwc,hwck->hwk', bary, mesh['pos'][t])
    n = np.einsum('hwc,hwck->hwk', bary, mesh['nrm'][t])
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
    region = np.asarray(Image.open(os.path.join(mdir, 'region.png')))
    # 1. One downsample.
    loaded = {}
    for role in ('base_color', 'metallic', 'roughness', 'normal'):
        image = Image.open(os.path.join(src, f'texture_urls_0_{role}.png'))
        image = image.convert('RGB') if role in ('base_color', 'normal') else image.convert('L')
        loaded[role] = image.resize((SIZE, SIZE), Image.LANCZOS)
    loaded['base_color'].save(os.path.join(out, 'base_color_2k.png'))
    # 2. Gentle grade on the AO bake.
    subprocess.run([sys.executable, os.path.join(SHARED, 'grade_basecolor.py'), os.path.join(out, 'base_color_2k.png'),
                    '--ao', os.path.join(mdir, 'ao.png'), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5',
                    '--contrast', '1.06', '--saturation', '1.15'], check=True, stdout=subprocess.DEVNULL)
    colour = np.asarray(Image.open(os.path.join(out, 'base_color_2k_graded.png')).convert('RGB'), np.float64) / 255
    meshy_n = np.asarray(loaded['normal'], np.float64) / 127.5 - 1.0
    meshy_n[..., 1] *= -1.0
    mm = np.asarray(loaded['metallic'], np.float64) / 255
    rr = np.asarray(loaded['roughness'], np.float64) / 255
    ao = np.asarray(Image.open(os.path.join(mdir, 'ao.png')).convert('L'), np.float64) / 255

    soft = lambda mask, s=0.8: np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(s)), np.float64) / 255
    metal = soft(np.isin(region, METAL).astype(np.float64))
    steel = np.isin(region, STEEL) & inside
    blade = np.isin(region, BLADE) & inside
    edge = soft((region == R['edge']).astype(np.float64), 1.2) * blade
    gem = (region == R['gem']) & inside
    glow_region = (region == R['glow']) & inside
    metal[~inside] = 0
    metal_t = metal > 0.5
    if not job.startswith(f'{kind}_t{tier}_'):
        # A tier painted from another tier's paint (the image tool refused the low tier's masters): the low look by
        # region, keeping the paint's grain and wear. Steel and brass go dark forged iron with rust patches from the
        # 3D position, wood weathered grey-brown ash, leather worn rawhide.
        lum = colour @ np.array([0.299, 0.587, 0.114])
        rel = lambda m: lum - (np.median(lum[m]) if m.any() else 0.5)
        wood = (region == R['wood']) & inside
        hide = (region == R['leather']) & inside
        rustiness = np.clip(value_noise(p[..., 1] / 2.5 + 0.7 * p[..., 0], 11) * 0.6
                            + value_noise(p[..., 1] / 0.7 + 1.3 * p[..., 2], 12) * 0.4 - 0.25, 0, 1) * 1.6
        iron = np.clip((0.36 + 0.7 * rel(metal_t))[..., None] * np.array([0.95, 0.94, 0.93]), 0, 1)
        rust_col = np.clip((0.3 + 0.5 * rel(metal_t))[..., None] * np.array([1.25, 0.72, 0.42]), 0, 1)
        iron = iron * (1 - np.clip(rustiness, 0, 0.8)[..., None]) + rust_col * np.clip(rustiness, 0, 0.8)[..., None]
        ash = np.clip((0.46 + 0.8 * rel(wood))[..., None] * np.array([0.78, 0.68, 0.56]), 0, 1)
        rawhide = np.clip((0.36 + 0.8 * rel(hide))[..., None] * np.array([0.72, 0.55, 0.38]), 0, 1)
        colour = np.where(metal_t[..., None], iron, colour)
        colour = np.where(wood[..., None], ash, colour)
        colour = np.where(hide[..., None], rawhide, colour)
        rr = np.clip(rr * 0.6 + 0.35, 0, 1)

    # 3. Weave filter and steel albedo.
    blur = np.asarray(Image.fromarray((colour * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(FINE_SIGMA)),
                      np.float64) / 255
    keep = (1 - metal + metal * cfg['fine'])[..., None]
    colour = blur + (colour - blur) * keep
    mx, mn = colour.max(-1), colour.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    hue = np.degrees(np.arctan2(np.sqrt(3) * (colour[..., 1] - colour[..., 2]),
                                2 * colour[..., 0] - colour[..., 1] - colour[..., 2])) % 360
    # 5a. Luminous inlays (legendary): bright saturated cyan to blue paint on metal.
    runes = np.zeros(inside.shape)
    if tier == 4:
        # Cyan to teal (hue 160-215: the navy-tinted dark metal is about 220-230 and less saturated).
        runes = np.where(metal_t, smoothstep(0.42, 0.62, sat) * smoothstep(0.28, 0.48, mx)
                         * ((hue > 160) & (hue < 215)), 0.0)
        runes = soft(runes, 0.6)
    lin = srgb_to_linear(colour)
    lum = lin @ np.array([0.2126, 0.7152, 0.0722])
    steel_metal = steel & metal_t & (runes < 0.3)
    median = max(np.median(lum[steel_metal]), 1e-3) if steel_metal.any() else 1.0
    rust = np.zeros(inside.shape)
    if cfg['rust']:
        hue_red = (colour[..., 0] >= colour[..., 1]) & (colour[..., 1] >= colour[..., 2]) & (
            (colour[..., 1] - colour[..., 2]) < 0.75 * (colour[..., 0] - colour[..., 2]))
        rust = np.where(metal_t & hue_red, smoothstep(0.25, 0.45, sat), 0.0)
    target = cfg['metal_lum'] * (np.maximum(lum, 1e-4) / median) ** CONTRAST
    lifted = np.minimum(lin * (target / np.maximum(lum, 1e-4))[..., None], 0.95)
    m3 = (metal * steel * (1 - rust) * (1 - runes))[..., None]
    lin = lin * (1 - m3) + lifted * m3
    # Brass and gold: a floor on their luminance (Meshy paints gilding dark in places), their hue kept.
    brass = (region == R['brass']) & inside
    if tier > 1 and brass.any():
        floor = 0.22
        gain = np.maximum(floor / np.maximum(lum, 1e-4), 1.0)
        lin = np.where(brass[..., None], np.minimum(lin * gain[..., None], 0.95), lin)

    # 4. Blades.
    lo_r, hi_r = np.percentile(rr[metal_t], [5, 95]) if metal_t.any() else (0, 1)
    r_metal = cfg['rough'][0] + (cfg['rough'][1] - cfg['rough'][0]) * np.clip((rr - lo_r) / max(hi_r - lo_r, 1e-3),
                                                                              0, 1)
    coord = p[..., 0] / 0.25 + value_noise(p[..., 1] / 3.0, 3) * 2.0
    grain = np.where(blade, 0.6 * value_noise(coord, 1) + 0.4 * value_noise(coord * 2.3, 2), 0.0)
    slow = np.where(blade, value_noise(p[..., 1] / 6.0 + 0.3 * p[..., 0], 7), 0.0)
    r_metal = r_metal * (1 - (1 - cfg['edge']) * edge) + 0.05 * grain + 0.1 * slow
    lin = lin * (1 + (0.4 * edge + 0.08 * grain + 0.08 * slow)[..., None] * (1 - runes[..., None]))
    rough = np.where(metal_t, r_metal, np.clip(rr, 0.35, 1.0))
    rough = rough * (1 - rust) + 0.85 * rust
    rough = rough * (1 - runes) + 0.3 * runes
    rough = np.where(gem, np.minimum(rough, 0.18), rough)
    metal = metal * (1 - 0.8 * rust) * (1 - runes)
    metallic = metal * (0.85 + 0.15 * mm) + (1 - metal) * 0.03 * mm

    # 5b. Emission.
    emission = np.zeros_like(lin)
    emission += lin * runes[..., None] * 2.5
    if kind == 'wand':
        # The crystal's glow by tier (WAND_GLOW): the paint's hue pushed to full saturation, its light facets brighter.
        hue_lin = lin / np.maximum(lin.max(-1, keepdims=True), 1e-4)
        tint = np.clip(hue_lin ** 1.6, 0.0, 1.0) * 0.85 + 0.15 * hue_lin
        if tier == 1:
            # The cloudy grey quartz: a faint cool blue-white.
            tint = np.broadcast_to(np.array([0.45, 0.7, 1.0]), lin.shape)
        z0, z1 = WAND_GLOW['span']
        along = np.clip((p[..., 1] - z0) / (z1 - z0), 0.0, 1.0)
        facet = np.clip(lum / max(np.percentile(lum[gem], 90), 1e-4), 0.0, 1.0) if gem.any() else lum
        level = WAND_GLOW['tiers'][tier] * (0.4 + 0.6 * smoothstep(0.0, 0.8, along)) * (0.3 + 0.7 * facet ** 1.5)
        emission += np.where(gem[..., None], tint * level[..., None], 0.0)
    else:
        emission += np.where(gem[..., None], lin * cfg['gem_glow'] * 1.5, 0.0)
    emission += np.where(glow_region[..., None], lin * 1.2, 0.0)
    has_emission = emission.max() > 0.02

    # Normal: Meshy's detail and the grain tilt, in each texel's tangent frame.
    tx, ty = tangent_frames(mesh, tid, inside, n)
    tilt = np.zeros_like(n)
    slope = (value_noise(coord + 0.05, 1) - value_noise(coord - 0.05, 1)) * 6.0
    tilt[..., 0] = np.where(blade, slope * 0.08, 0.0)
    world = n + tilt
    world /= np.maximum(np.linalg.norm(world, axis=-1, keepdims=True), 1e-9)
    ts = np.stack([np.sum(world * tx, -1), np.sum(world * ty, -1), np.sum(world * n, -1)], -1)
    soft_n = meshy_n * np.array([0.15, 0.15, 1.0])
    soft_n /= np.maximum(np.linalg.norm(soft_n, axis=-1, keepdims=True), 1e-9)
    blend = np.stack([soft_n[..., 0] + ts[..., 0], soft_n[..., 1] + ts[..., 1], soft_n[..., 2] * ts[..., 2]], -1)
    blend /= np.maximum(np.linalg.norm(blend, axis=-1, keepdims=True), 1e-9)
    normal = np.where(blade[..., None], blend, meshy_n)
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-9)

    # 5c. Legendary poles: the shaft's ebony, rune channels and collar stones drawn from the 3D position (shaft_runes.py).
    shaft = {}
    if tier == 4:
        sys.path.insert(0, HERE)
        import shaft_runes
        if kind in shaft_runes.POLES:
            shaft = shaft_runes.apply(p, n, region, inside, lin, rough, metallic, emission, normal, tx, ty, R)
            has_emission = True

    # 6. Maps, gutters, GLB.
    files = {'basecolor': os.path.join(out, 'basecolor.png'), 'normal': os.path.join(out, 'normal.png'),
             'mr': os.path.join(out, 'mr.png')}
    Image.fromarray((linear_to_srgb(lin) * 255 + 0.5).astype(np.uint8)).save(files['basecolor'])
    Image.fromarray(np.clip((normal + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)).save(files['normal'])
    mr = np.stack([np.clip(0.35 + 0.65 * ao, 0, 1), np.clip(rough, 0.05, 1), np.clip(metallic, 0, 1)], -1)
    Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).resize((SIZE // 2, SIZE // 2), Image.LANCZOS).save(files['mr'])
    if has_emission:
        files['emissive'] = os.path.join(out, 'emissive.png')
        Image.fromarray((linear_to_srgb(np.clip(emission, 0, 1)) * 255 + 0.5).astype(np.uint8)).save(
            files['emissive'])
    np.savez(os.path.join(mdir, 'uv_tris.npz'), uv=mesh['uv'])
    subprocess.run([sys.executable, os.path.join(SHARED, 'gutter_fill.py'), os.path.join(mdir, 'uv_tris.npz')]
                   + list(files.values()) + ['--in-place'], check=True, stdout=subprocess.DEVNULL)
    glb = os.path.join(out, f'w_{kind}_t{tier}.glb')
    tris, verts = write_glb(glb, kind, tier, mesh, files, shaft.get('emissive_strength'))
    stats = {'tris': tris, 'verts': verts, 'metal_share': round(float(metal_t[inside].mean()), 3),
             'steel_median_before': round(float(median), 3), 'rust_share': round(float((rust > 0.5)[inside].mean()), 3),
             'rune_share': round(float((runes > 0.5)[inside].mean()), 4), 'emissive': bool(has_emission),
             'rough_metal_p10_p50_p90': np.percentile(rough[metal_t], [10, 50, 90]).round(2).tolist(),
             'glb_mb': round(os.path.getsize(glb) / 1e6, 2), **shaft}
    json.dump(stats, open(os.path.join(out, 'post.json'), 'w'), indent=1)
    print('SKIN', kind, tier, json.dumps(stats))


if __name__ == '__main__':
    if sys.argv[1] == 'maps':
        maps(sys.argv[2])
    else:
        skin(sys.argv[2], sys.argv[3], sys.argv[4])
