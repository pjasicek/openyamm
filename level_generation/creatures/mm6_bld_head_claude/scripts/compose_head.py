#!/usr/bin/env python3
"""Bloodsucker head texture set from the Meshy head retexture (CLAUDE_CREATURE_TEXTURES.md "Head detail").

In:  meshy/head_texture/*.glb (Meshy return, head UVs), work/head_uv.json (dump_head_uv.py), references_head/04_maw.png,
     the installed body set ../mm6_bld_claude/textures (tier-A graded base and its region weights).
Out: textures/bld_head_{basecolor_graded,normal_1k,metal_rough_1k,region_mask}.png, bld_head_region_weights.npz,
     bld_head_material_classes.png, textures/bld_ramps.json (body + head, shared ramps), work/compose_head.json.

- Regions come from the new texture's own colours (never the old mask): teal/dark hide -> body, salmon/red throat and
  belly stripe -> maw, ivory teeth/spikes and the cyan eyes -> none. The maw island takes the painted maw art
  (04_maw.png) and is the `disc` region.
- Each region's luminance is quantile-matched to the same region of the installed tier-A body texture, so the accepted
  body ramps recolour the head the same way (merge_head_material.py requires equal ramps).
- Maps are nearest-padded beyond the islands before the 2K -> 1K downsize, and the mask is padded the same way."""
import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
BODY = HERE.parent / 'mm6_bld_claude' / 'textures'
T = HERE / 'textures'
SIZE, WORK = 1024, 2048
EYE_RADIUS = 0.011            # m, rest pose
BAND_SIGMA, DETAIL = 10.0, 0.7  # texels at 2K; exponent of the fine detail kept on top of the matched bands
LUMA = np.array([0.2126, 0.7152, 0.0722])


def lin(s):
    return np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)


def enc(v):
    v = np.clip(v, 0, 1)
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * v ** (1 / 2.4) - 0.055)


def glb_images(path):
    raw = path.read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + n])
    binary = raw[28 + n:]
    out = {}
    for mat in doc['materials']:
        pbr = mat.get('pbrMetallicRoughness', {})
        for key, ref in (('base', pbr.get('baseColorTexture')), ('mr', pbr.get('metallicRoughnessTexture')),
                         ('normal', mat.get('normalTexture'))):
            if ref is None:
                continue
            image = doc['images'][doc['textures'][ref['index']]['source']]
            view = doc['bufferViews'][image['bufferView']]
            start = view.get('byteOffset', 0)
            out[key] = Image.open(io.BytesIO(binary[start:start + view['byteLength']]))
    return out


def raster(tris, kinds, size):
    image = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(image)
    for tri in tris:
        if tri['kind'] in kinds:
            draw.polygon([(u * size, (1 - v) * size) for u, v in tri['uv']], fill=255)
    return np.asarray(image) > 127


def position_map(tris, kinds, size):
    """Rest-pose 3D position per texel of the given triangles (barycentric), and the covered texels."""
    pos = np.zeros((size, size, 3))
    has = np.zeros((size, size), bool)
    for tri in tris:
        if tri['kind'] not in kinds:
            continue
        uv = np.array(tri['uv']) * size
        uv[:, 1] = size - uv[:, 1]
        co = np.array(tri['co'])
        x0, y0 = np.floor(uv.min(0)).astype(int)
        x1, y1 = np.ceil(uv.max(0)).astype(int)
        ys, xs = np.mgrid[max(y0, 0):min(y1 + 1, size), max(x0, 0):min(x1 + 1, size)]
        p = np.stack([xs + 0.5, ys + 0.5], -1)
        a, b, c = uv
        m = np.array([b - a, c - a]).T
        if abs(np.linalg.det(m)) < 1e-12:
            continue
        l12 = np.linalg.solve(m, (p - a).reshape(-1, 2).T).T.reshape(p.shape)
        l0 = 1 - l12[..., 0] - l12[..., 1]
        inside = (l0 >= -1e-3) & (l12[..., 0] >= -1e-3) & (l12[..., 1] >= -1e-3)
        bary = np.stack([l0, l12[..., 0], l12[..., 1]], -1)
        pos[ys[inside], xs[inside]] = bary[inside] @ co
        has[ys[inside], xs[inside]] = True
    return pos, has


def pad(rgb, covered):
    """Nearest covered texel into every uncovered one."""
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return rgb[iy, ix]


def main():
    uvs = json.loads((HERE / 'work' / 'head_uv.json').read_text())
    returns = sorted((HERE / 'meshy' / 'head_texture').glob('*.glb'))
    maps = glb_images(returns[-1])
    hide = raster(uvs['tris'], {0}, WORK)
    inner = raster(uvs['tris'], {1}, WORK)
    island = hide | inner
    base = np.asarray(maps['base'].convert('RGB').resize((WORK, WORK), Image.LANCZOS), dtype=np.float64) / 255

    # maw art into the inner island (the outer shell samples its rim band)
    art = Image.open(HERE / 'references_head' / '04_maw.png').convert('RGBA')
    alpha = np.asarray(art)[..., 3] > 127
    ys, xs = np.nonzero(alpha)
    acx, acy, ar = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2, (xs.max() - xs.min() + ys.max() - ys.min()) / 4
    art_rgb = np.asarray(art.convert('RGB'), dtype=np.float64) / 255
    mc, mr = uvs['maw_uv_centre'], uvs['maw_uv_radius']
    yy, xx = np.mgrid[0:WORK, 0:WORK]
    u, v = (xx + 0.5) / WORK, 1 - (yy + 0.5) / WORK
    du, dv = (u - mc[0]) / mr, (v - mc[1]) / mr
    disc = (du * du + dv * dv <= 1.0) & island
    ax = np.clip(acx + du * ar * 0.995, 0, art.width - 1)
    ay = np.clip(acy - dv * ar * 0.995, 0, art.height - 1)
    base[disc] = np.stack([ndimage.map_coordinates(art_rgb[..., c], [ay[disc], ax[disc]], order=1)
                           for c in range(3)], -1)

    # eyes: Meshy painted none; round eyes where the installed model had them (work/eyes.json, rest pose), mirrored,
    # kept out of every tier region so they keep the installed eye colour
    pos, has = position_map(uvs['tris'], {0}, WORK)
    eyes = json.loads((HERE / 'work' / 'eyes.json').read_text())
    centre = np.mean([np.array(e['centre']) * np.array([np.sign(e['centre'][0]), 1, 1]) for e in eyes], axis=0)
    eye_weight = np.zeros((WORK, WORK))
    for side in (1, -1):
        c = centre * np.array([side, 1, 1])
        d = np.linalg.norm(pos - c, axis=-1) / EYE_RADIUS
        inside = has & (d < 1.0)
        # dark pupil, bright orange-salmon iris (the installed eye colour), dark rim; outside every tier region
        colour = np.where((d < 0.35)[..., None], [0.16, 0.08, 0.07],
                          np.where((d < 0.8)[..., None], [0.92, 0.6, 0.47], [0.24, 0.13, 0.1]))
        base[inside] = colour[inside]
        eye_weight[inside] = 1.0

    # regions from the new colours
    hsv = np.asarray(Image.fromarray((base * 255).astype(np.uint8)).convert('HSV'), dtype=np.float64) / 255
    h, s, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    ivory = (s < 0.28) & (val > 0.55)
    eye = (h > 165) & (h < 205) & (s > 0.45) & (val > 0.7)
    eye = eye | (eye_weight > 0)
    red = ((h < 25) | (h > 335)) & (s > 0.3) & ~ivory & ~eye
    hide_tex = hide & ~disc
    regions = {'body': (hide_tex & ~ivory & ~eye & ~red).astype(np.float64),
               'wing': np.zeros((WORK, WORK)),
               'maw': (hide_tex & red).astype(np.float64),
               'disc': disc.astype(np.float64)}
    classes = np.zeros((WORK, WORK), np.uint8)
    classes[hide_tex] = 1
    classes[hide_tex & red] = 7
    classes[hide_tex & ivory] = 5
    classes[hide_tex & eye] = 6
    classes[disc] = 7

    # luminance of each region matched to the installed tier-A body texture's same region
    body = np.asarray(Image.open(BODY / 'bld_a_basecolor_graded.png').convert('RGB'), dtype=np.float64) / 255
    weights = np.load(BODY / 'bld_region_weights.npz')
    body_lum = lin(body) @ LUMA
    lin_base = lin(base)
    lum = lin_base @ LUMA
    report = {}
    for name in ('body', 'maw', 'disc'):
        core = regions[name] > 0.5
        target = np.sort(body_lum[np.asarray(weights[name]) > 0.9])
        if core.sum() < 100 or len(target) < 100:
            report[name] = 'skipped'
            continue
        src = lum[core]
        if name == 'disc':
            # the painted maw keeps its own contrast (bright teeth, salmon ring, dark throat): one gain to the old
            # disc's median, clipped to the region's top
            gain = np.median(target) / max(np.median(src), 1e-5)
            matched = np.minimum(src * gain, target[-1])
            lin_base[core] *= (matched / np.maximum(src, 1e-5))[:, None]
            report[name] = {'texels': int(core.sum()), 'gain': round(float(gain), 3)}
            continue
        # rank the smoothed luminance, so broad bands (not fine scale noise) take the body's dark and light tones;
        # the fine detail rides on top as a damped ratio
        weight = core.astype(np.float64)
        smooth = ndimage.gaussian_filter(lum * weight, BAND_SIGMA) / np.maximum(ndimage.gaussian_filter(weight, BAND_SIGMA), 1e-6)
        low = smooth[core]
        ranks = np.argsort(np.argsort(low)) / max(len(low) - 1, 1)
        matched = target[np.minimum((ranks * (len(target) - 1)).round().astype(int), len(target) - 1)]
        if name == 'body':
            matched = matched * (src / np.maximum(low, 1e-5)) ** DETAIL
        else:
            matched = matched * src / np.maximum(low, 1e-5)
        lin_base[core] *= (matched / np.maximum(src, 1e-5))[:, None]
        report[name] = {'texels': int(core.sum()), 'lum_before': round(float(np.median(src)), 4),
                        'lum_after': round(float(np.median(matched)), 4)}
    base = enc(lin_base)

    covered = island
    out = Image.fromarray((pad(base, covered) * 255 + 0.5).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS)
    T.mkdir(exist_ok=True)
    out.save(T / 'bld_head_basecolor_graded.png')
    normal = np.asarray(maps['normal'].convert('RGB').resize((WORK, WORK), Image.LANCZOS), dtype=np.float64)
    normal[disc] = (128, 128, 255)
    Image.fromarray(pad(normal, covered).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS).save(
        T / 'bld_head_normal_1k.png')
    mr = np.asarray(maps['mr'].convert('RGB').resize((WORK, WORK), Image.LANCZOS), dtype=np.float64)
    mr[..., 0] = 255
    mr[..., 2] = 0
    mr[disc, 1] = 150
    Image.fromarray(pad(mr, covered).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS).save(
        T / 'bld_head_metal_rough_1k.png')

    # region weights: padded like the colour, softened by about one texel, zero where no island owns the texel later
    padded = {name: pad(w[..., None], covered)[..., 0] for name, w in regions.items()}
    soft = {name: ndimage.gaussian_filter(w, 1.0) for name, w in padded.items()}
    names = ['body', 'wing', 'maw', 'disc']
    np.savez_compressed(T / 'bld_head_region_weights.npz', names=np.array(names), **soft)
    from sys import path as syspath
    syspath.insert(0, str(HERE.parent / 'claude_shared'))
    import region_variants as R
    R.write_mask([soft[name] for name in names], T / 'bld_head_region_mask.png', SIZE)
    Image.fromarray(classes).resize((SIZE, SIZE), Image.NEAREST).save(T / 'bld_head_material_classes.png')

    # ramps: the body's material entry plus an identical head entry with its own mask
    ramps = json.loads((BODY / 'bld_ramps.json').read_text())
    body_entry = ramps['materials'][0]
    head_entry = dict(body_entry, base='BldHead_A', prefix='BldHead', mask='bld_head_region_mask.png')
    ramps['materials'] = [body_entry, head_entry]
    (T / 'bld_ramps.json').write_text(json.dumps(ramps, indent=1) + '\n')
    Image.open(BODY / 'bld_a_basecolor_graded.png').resize((SIZE, SIZE), Image.LANCZOS).save(
        T / 'bld_a_basecolor_graded_1k.png')            # body base at 1K beside the 1K head set
    for name in ('bld_region_mask.png',):
        (T / name).write_bytes((BODY / name).read_bytes())
    (HERE / 'work' / 'compose_head.json').write_text(json.dumps({'source': str(returns[-1].name), 'regions': report},
                                                                indent=1) + '\n')
    print('COMPOSED', json.dumps(report))


if __name__ == '__main__':
    main()
