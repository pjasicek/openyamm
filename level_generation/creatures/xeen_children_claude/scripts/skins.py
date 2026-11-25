#!/usr/bin/env python3
"""XD-04's four caged children (D-163, the user: "you can generate new skins for them"): masks, ramps and the
add_variants.py specs for the Xeen copies of MM9's elf-eared boy and girl.

Usage: skins.py <work dir>   (writes <work>/img, textures/*.png, <work>/boy.json, ears.json, girl.json, previews)

Skins (ramps only, CLAUDE_CREATURE_TEXTURES.md; no new paint):
  xboy_ginger  child 1, the Goblin-eared boy of npc 4053's portrait: boy e's freckled head with its hair ramped to
               bright ginger, grey-brown homespun vest, undyed linen shirt, dark brown breeches; ears faintly green.
  xboy_dark    child 3: boy b's dark-haired head, moss-green vest, cream shirt, russet breeches; ears as above.
  xgirl_rose   child 2, Rosebud: madder-rose dress, linen trims, her own light brown hair.
  xgirl_flax   child 4: woad-blue dress, brown trims, flaxen hair.
Each target is the base texel's own brightness in the new hue and saturation (V times a gain); fit_ramps turns it
into the region's 16-stop ramp.
"""
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
from hsv import hsv_to_rgb, rgb_to_hsv  # noqa: E402
from region_variants import fit_ramps, read_glb, srgb_to_linear, write_mask  # noqa: E402

BOY = ROOT / 'assets_source/worlds/mm9/models/mm9_peasantboy.glb'
EARS = ROOT / 'assets_source/worlds/mm9/models/mm9_peasantboy_elfears.glb'
GIRL = ROOT / 'assets_source/worlds/mm9/models/mm9_peasantgirl1e.glb'


def images(path):
    doc, binary = read_glb(path)
    found = {}
    for image in doc['images']:
        view = doc['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        found[image['name']] = Image.open(io.BytesIO(binary[start:start + view['byteLength']])).convert('RGBA')
    return found


def srgb(image, size=None):
    if size is not None and image.size != size:
        image = image.resize(size, Image.LANCZOS)
    return np.asarray(image.convert('RGB'), dtype=np.float64) / 255.0


def recolour(base, hue, sat, gain, mix=1.0):
    """The base texels' own brightness in a new hue and saturation (V x gain), blended by mix."""
    hsv = rgb_to_hsv(base)
    target = np.stack([np.full(hsv.shape[:2], hue), np.full(hsv.shape[:2], sat),
                       np.clip(hsv[..., 2] * gain, 0, 1)], -1)
    return np.clip(base * (1 - mix) + hsv_to_rgb(target) * mix, 0, 1)


def ramp(base, weight, hue, sat, gain, mix=1.0, name=''):
    ramps, report = fit_ramps(base, {'v': recolour(base, hue, sat, gain, mix)}, weight)
    print(f'  {name}: fit mean {report["v"]["mean_abs_8bit"]} p95 {report["v"]["p95_abs_8bit"]}, '
          f'{report["core_texels"]} core texels')
    return ramps['v']


def apply(base, weights, ramps):
    """CPU preview of the shader: per region, t from linear luminance, the ramp mixed in by the mask channel."""
    lum = srgb_to_linear(base) @ np.array([0.2126, 0.7152, 0.0722])
    out = srgb_to_linear(base)
    for weight, entry in zip(weights, ramps):
        lo, hi = entry['range']
        colors = np.asarray(entry['colors'])
        x = np.clip((lum - lo) / (hi - lo), 0, 1) * 15
        i0 = np.minimum(np.floor(x).astype(int), 14)
        f = (x - i0)[..., None]
        value = colors[i0] * (1 - f) + colors[i0 + 1] * f
        out = out * (1 - weight[..., None]) + value * weight[..., None]
    return np.where(out <= 0.0031308, out * 12.92, 1.055 * np.maximum(out, 0) ** (1 / 2.4) - 0.055)


def save(array, path, size=None):
    image = Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8))
    if size:
        image = image.resize(size, Image.LANCZOS)
    image.save(path)


def hair_weight(head):
    """Hair (and brows) of a head set: warm, saturated, not bright; skin, eyes, lips and the collar pieces stay out."""
    hsv = rgb_to_hsv(head)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    hard = ((h > 12) & (h < 50) & (s > 0.55) & (v < 0.8)).astype(np.uint8) * 255
    # feathered inward only: a skin texel next to the hair keeps weight 0 (an outward blur drew an orange rim
    # round the face, its bright skin luminance taking the top of the hair ramp)
    soft = np.asarray(Image.fromarray(hard).filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float64) / 255.0
    return soft * (hard > 0)


def region_weights(mask):
    array = np.asarray(mask, dtype=np.float64) / 255.0
    return [array[..., i] for i in range(4)]


def main():
    work = Path(sys.argv[1])
    (work / 'img').mkdir(parents=True, exist_ok=True)
    textures = PROJECT / 'textures'
    textures.mkdir(exist_ok=True)

    print('boy')
    boy = images(BOY)
    body = srgb(boy['pboy_tp_basecolor_graded'], (1024, 1024))
    weights = region_weights(boy['pboy_region_mask'])
    region_names = ['vest', 'shirt', 'breeches', 'belt']
    boy_body = {
        # grey-brown homespun, undyed linen, dark brown breeches, dark leather (npc 4053's portrait shirt)
        'xboy_ginger': [(32, 0.22, 1.05), (38, 0.14, 0.95), (24, 0.42, 0.9), (22, 0.45, 0.85)],
        # moss-green vest, cream shirt, russet breeches, brown belt
        'xboy_dark': [(88, 0.30, 1.2), (42, 0.20, 1.0), (16, 0.55, 1.15), (26, 0.5, 0.9)],
    }
    body_ramps = {}
    for variant, looks in boy_body.items():
        body_ramps[variant] = [ramp(body, w, *look, name=f'{variant} {n}')
                               for w, look, n in zip(weights, looks, region_names)]
        save(apply(body, weights, body_ramps[variant]), work / 'img' / f'body_{variant}.png', (768, 768))

    head_e = srgb(boy['pboye_tp_head_basecolor'], (1024, 1024))
    hair = hair_weight(head_e)
    write_mask([hair], textures / 'xboy_ginger_head_mask.png', 1024)
    # npc 4053: bright copper-ginger, lighter than boy e's auburn
    ginger = ramp(head_e, hair, 25, 0.76, 1.75, name='xboy_ginger hair')
    save(apply(head_e, [hair], [ginger]), work / 'img' / 'head_xboy_ginger.png', (1024, 1024))

    boy_spec = {'variants': [
        {'name': 'xboy_ginger', 'materials': {
            'PeasantBoy_A': {'from': 'PeasantBoy_A', 'ramps': body_ramps['xboy_ginger']},
            'PeasantBoyHead': {'from': 'PeasantBoyHead_pboy_e', 'ramps': [ginger],
                               'mask': str(textures / 'xboy_ginger_head_mask.png')}}},
        {'name': 'xboy_dark', 'materials': {
            'PeasantBoy_A': {'from': 'PeasantBoy_A', 'ramps': body_ramps['xboy_dark']},
            'PeasantBoyHead': {'from': 'PeasantBoyHead_pboy_b', 'ramps': None}}},
    ]}
    (work / 'boy.json').write_text(json.dumps(boy_spec, indent=1))

    print('ears')
    ears = images(EARS)
    ear = next(v for k, v in ears.items() if 'basecolor' in k)
    size = (ear.size[0] // 2, ear.size[1] // 2)
    ear_rgb = srgb(ear, size)
    whole = np.ones(ear_rgb.shape[:2])
    write_mask([whole], textures / 'xboy_ears_mask.png', size)
    # a faint goblin green on the skin's own shading (the portrait's ears are yellow-green)
    green = ramp(ear_rgb, whole, 66, 0.42, 0.92, mix=0.75, name='ears green')
    save(apply(ear_rgb, [whole], [green]), work / 'img' / 'ears_green.png')
    ears_spec = {'variants': [
        {'name': v, 'materials': {'PeasantBoyHead': {'from': 'PeasantBoyHead', 'ramps': [green],
                                                     'mask': str(textures / 'xboy_ears_mask.png')}}}
        for v in ('xboy_ginger', 'xboy_dark')]}
    (work / 'ears.json').write_text(json.dumps(ears_spec, indent=1))

    print('girl')
    girl = images(GIRL)
    gbody = srgb(girl['pg_body_tone'], (1024, 1024))
    gweights = region_weights(girl['pg_body_mask'])[:3]
    doc, _ = read_glb(GIRL)
    g1e = next(m for m in doc['materials'] if m['name'] == 'PeasantGirl_G1E')['extras']['openyamm_region_ramps']
    girl_body = {
        'xgirl_rose': [(352, 0.48, 1.3), (40, 0.18, 1.25)],     # madder-rose dress, linen trims
        'xgirl_flax': [(214, 0.42, 1.45), (24, 0.45, 0.85)],    # woad-blue dress, brown trims
    }
    girl_ramps = {}
    for variant, looks in girl_body.items():
        girl_ramps[variant] = [ramp(gbody, w, *look, name=f'{variant} {n}')
                               for w, look, n in zip(gweights, looks, ['dress', 'trims'])] + [g1e[2]]
        save(apply(gbody, gweights, girl_ramps[variant]), work / 'img' / f'body_{variant}.png', (768, 768))
    ghead = srgb(girl['pg_head_g1e_fix'], (1024, 1024))
    ghair = hair_weight(ghead)
    write_mask([ghair], textures / 'xgirl_flax_head_mask.png', 1024)
    flax = ramp(ghead, ghair, 40, 0.52, 1.6, name='xgirl_flax hair')
    save(apply(ghead, [ghair], [flax]), work / 'img' / 'head_xgirl_flax.png')
    girl_spec = {'variants': [
        {'name': 'xgirl_rose', 'materials': {
            'PeasantGirl_G1E': {'from': 'PeasantGirl_G1E', 'ramps': girl_ramps['xgirl_rose']}}},
        {'name': 'xgirl_flax', 'materials': {
            'PeasantGirl_G1E': {'from': 'PeasantGirl_G1E', 'ramps': girl_ramps['xgirl_flax']},
            'PeasantGirlHead': {'from': 'PeasantGirlHead', 'ramps': [flax],
                                'mask': str(textures / 'xgirl_flax_head_mask.png')}}},
    ]}
    (work / 'girl.json').write_text(json.dumps(girl_spec, indent=1))


if __name__ == '__main__':
    main()
