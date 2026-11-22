#!/usr/bin/env python3
"""Add a body region to a Xeen tier copy (decision D-10, 2026-11-20): a new region-mask channel classified from the
shared base colour, and a ramp for it on every material that uses the mask, so a tier can recolour a surface its source
model's mask missed (golem bodies, ogre armour, werewolf fur, orc skin). Mesh, clips, LODs and the base colour stay.

    add_region.py <in.glb> <out.glb> <spec.json> [--mask-preview DIR]

spec.json:
  {"channel": 2,                               # the new channel: the materials' ramp count (R=0 G=1 B=2 A=3)
   "classify": [{"hue": [lo, hi], "sat": [lo, hi], "val": [lo, hi]}, ...],   # HSV boxes (deg, 0..1), union
   "uv_rects": [[u0, v0, u1, v1], ...],        # optional: keep only texels inside these UV rectangles (LOD0 atlas)
   "exclude_channels": [0, 1],                 # texels already in these channels (above 0.3) stay out
   "feather": 1,                               # box blur radius in texels
   "skins": {"<skin>": {"mid": "#rrggbb", "contrast": k, "lift": l, "shadow": "#rrggbb", "highlight": "#rrggbb"}}}

Every material carrying the mask gets one more ramp. A skin listed in "skins" gets its colour: the region's average
shown colour becomes `mid` (xeen_tiers.py's rule: each stop = target x its luminance ratio to the region's mean
luminance, `contrast` and `lift` as there); optional `shadow`/`highlight` change the hue of the dark/light stops
(stops 0-7 blend shadow -> mid, 8-15 mid -> highlight) at the same luminance. Every other skin gets the ramp fitted to
the base colour itself (claude_shared/region_variants.fit_ramps), so it keeps its current look. Each LOD's own base and
mask textures are classified alike (they were baked from LOD0; their gutters are already nearest-texel filled, so the
mask is padded by construction).
"""
import colorsys
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import xeen_tiers as xt                       # noqa: E402
import region_variants as rv                  # noqa: E402


def image_bytes(doc, binary, image_index):
    view = doc['bufferViews'][doc['images'][image_index]['bufferView']]
    start = view.get('byteOffset', 0)
    return binary[start:start + view['byteLength']]


def replace_image(doc, binary, image_index, data):
    """Append new image bytes at the buffer end and point the image's bufferView there (the old bytes are dropped by
    the final repack)."""
    pad = (-len(binary)) % 4
    binary = binary + b'\0' * pad
    view = doc['bufferViews'][doc['images'][image_index]['bufferView']]
    view['byteOffset'] = len(binary)
    view['byteLength'] = len(data)
    view.pop('byteStride', None)
    binary = binary + data
    doc['buffers'][0]['byteLength'] = len(binary)
    return binary


def classify(base_rgb, rules):
    hsv = np.asarray(Image.fromarray((base_rgb * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    out = np.zeros(base_rgb.shape[:2], bool)
    for r in rules:
        hl, hh = r.get('hue', [0, 360]); sl, sh = r.get('sat', [0, 1]); vl, vh = r.get('val', [0, 1])
        hue_ok = (h >= hl) & (h <= hh) if hl <= hh else (h >= hl) | (h <= hh)
        out |= hue_ok & (s >= sl) & (s <= sh) & (v >= vl) & (v <= vh)
    return out


def stop_targets(rule):
    mid = np.array(xt.srgb_hex_to_linear(rule['mid']))
    lo = np.array(xt.srgb_hex_to_linear(rule.get('shadow', rule['mid'])))
    hi = np.array(xt.srgb_hex_to_linear(rule.get('highlight', rule['mid'])))
    out = []
    for i in range(16):
        c = lo + (mid - lo) * (i / 8) if i < 8 else mid + (hi - mid) * ((i - 8) / 7)
        c = c * (xt.luminance(mid) / max(xt.luminance(c), 1e-6))     # hue only: the luminance stays mid's
        out.append(c)
    return out


def coloured_ramp(identity, rule, reference):
    targets = stop_targets(rule)
    contrast, lift = rule.get('contrast', 1.0), rule.get('lift', 0.0)
    colors = []
    for c, tgt in zip(identity['colors'], targets):
        k = lift + (1 - lift) * (max(xt.luminance(c), 0.0) / max(reference, 1e-5)) ** contrast
        colors.append([round(float(min(1.0, x * k)), 6) for x in tgt])
    return {'range': identity['range'], 'colors': colors}


def main(src, dst, spec_path, preview_dir=None):
    doc, binary = xt.read(src)
    spec = json.load(open(spec_path))
    ch = spec['channel']
    variants = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
    mat_skins = {}
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for m in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                mat_skins.setdefault(m['material'], set()).update(variants[i] for i in m['variants'])
    # group materials by (base texture, mask texture): one classification per LOD atlas
    groups = {}
    for mi, mat in enumerate(doc['materials']):
        ex = mat.get('extras', {})
        if 'openyamm_region_mask' not in ex:
            continue
        key = (mat['pbrMetallicRoughness']['baseColorTexture']['index'], ex['openyamm_region_mask']['index'])
        groups.setdefault(key, []).append(mi)
    for gi, ((base_tex, mask_tex), mats) in enumerate(sorted(groups.items())):
        base_img = Image.open(io.BytesIO(image_bytes(doc, binary, doc['textures'][base_tex]['source']))).convert('RGB')
        mask_index = doc['textures'][mask_tex]['source']
        mask_img = Image.open(io.BytesIO(image_bytes(doc, binary, mask_index))).convert('RGBA')
        base = np.asarray(base_img, np.float64) / 255
        H, Wd = base.shape[:2]
        mask_full = np.asarray(mask_img.resize((Wd, H), Image.BILINEAR), np.float64) / 255
        sel = classify(base, spec['classify'])
        for c in spec.get('exclude_channels', []):
            sel &= mask_full[..., c] < 0.3
        if spec.get('uv_rects') and gi == 0:
            uu, vv = np.meshgrid((np.arange(Wd) + 0.5) / Wd, (np.arange(H) + 0.5) / H)
            keep = np.zeros_like(sel)
            for u0, v0, u1, v1 in spec['uv_rects']:
                keep |= (uu >= u0) & (uu <= u1) & (vv >= v0) & (vv <= v1)
            sel &= keep
        weight = Image.fromarray((sel * 255).astype(np.uint8), 'L')
        if spec.get('feather', 1):
            weight = weight.filter(ImageFilter.BoxBlur(spec.get('feather', 1)))
        wfull = np.asarray(weight, np.float64) / 255
        for c in spec.get('exclude_channels', []):
            wfull = np.minimum(wfull, 1 - mask_full[..., c])
        # the new channel at the mask's own resolution
        mw, mh = mask_img.size
        wmask = np.asarray(Image.fromarray((wfull * 255 + 0.5).astype(np.uint8), 'L').resize((mw, mh), Image.BOX))
        arr = np.asarray(mask_img).copy()
        if arr[..., ch].max() > 0:
            raise SystemExit(f'mask texture {mask_tex}: channel {ch} is already used')
        arr[..., ch] = wmask
        out = io.BytesIO(); Image.fromarray(arr, 'RGBA').save(out, 'PNG', optimize=True)
        binary = replace_image(doc, binary, mask_index, out.getvalue())
        if preview_dir:
            Path(preview_dir).mkdir(parents=True, exist_ok=True)
            vis = (base * 0.35 * 255).astype(np.uint8); vis[..., 0] = np.maximum(vis[..., 0], (wfull * 255).astype(np.uint8))
            Image.fromarray(vis).save(Path(preview_dir) / f'mask_{gi}_tex{mask_tex}.png')
        # ramps
        identity, report = rv.fit_ramps(base, {'id': base}, wfull)
        identity = identity['id']
        lum = rv.luminance(base)[wfull >= 0.9]
        lo, hi = identity['range']
        t = np.clip((lum - lo) / max(hi - lo, 1e-4), 0, 1)
        stops = np.array([xt.luminance(c) for c in identity['colors']])
        reference = float(np.interp(t * 15, np.arange(16), stops).mean())
        print(f'group {gi}: base tex {base_tex} mask tex {mask_tex}: region {wfull.mean() * 100:.1f} % of the atlas, '
              f'identity fit {report["id"]}, reference luminance {reference:.4f}')
        for mi in mats:
            ex = doc['materials'][mi]['extras']
            ramps = ex['openyamm_region_ramps']
            if len(ramps) != ch:
                raise SystemExit(f'material {doc["materials"][mi]["name"]}: {len(ramps)} ramps, channel {ch}')
            skins = mat_skins.get(mi, set())
            rule = next((spec['skins'][s] for s in skins if s in spec.get('skins', {})), None)
            ramps.append(coloured_ramp(identity, rule, reference) if rule else identity)
    doc, binary = rv._compact(doc, bytes(binary))      # drops the replaced mask bytes
    xt.write(dst, doc, binary)
    print('WROTE', dst)


if __name__ == '__main__':
    args = sys.argv[1:]
    prev = None
    if '--mask-preview' in args:
        i = args.index('--mask-preview'); prev = args[i + 1]; del args[i:i + 2]
    main(*args[:3], preview_dir=prev)
