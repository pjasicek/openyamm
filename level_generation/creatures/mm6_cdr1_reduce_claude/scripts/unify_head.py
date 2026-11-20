#!/usr/bin/env python3
"""Head vs body colour (user 2026-10-14, after the same fix on the flying drake): the dragon's head and body tier
materials share their region ramps, but the head's base colour was much darker in both ramped regions (linear
luminance median: hide 0.080 vs the body's 0.159, belly 0.343 vs 0.447), so every tier's head read deeper than the
neck. Each ramped region's head luminance is quantile-matched to the body's distribution of the same region; each
texel is scaled by matched/original luminance (hue and scale detail kept), weighted by its mask value. Ivory, teeth
and eyes (outside the mask) are unchanged. Only the head base colour image changes (shared by the three head tier
materials). Usage: unify_head.py <in.glb> <out.glb>"""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent)); import glb_raster as G  # noqa: E402
from build_actor_lods import write_glb  # noqa: E402
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
W = np.array([.2126, .7152, .0722])
REGIONS = (0, 1)     # hide, belly
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = G.read_glb(src); binary = bytearray(binary)
mats = {m['name']: m for m in doc['materials']}
prims = G.lod0_primitives(doc, binary, 'Body')


def load(name):
    m = mats[name]
    base = np.asarray(G.image(doc, binary, m['pbrMetallicRoughness']['baseColorTexture']['index']).convert('RGB'), np.float32) / 255
    mask = np.asarray(G.image(doc, binary, m['extras']['openyamm_region_mask']['index']).convert('RGBA')
                      .resize(base.shape[1::-1], Image.Resampling.BILINEAR), np.float32) / 255
    _, cov = G.raster(prims[name]['pos'], prims[name]['uv'], prims[name]['idx'], base.shape[0])
    return base, mask, cov


bbase, bmask, bcov = load('DragonBody_A')
hbase, hmask, hcov = load('DragonHead_A')
bl, hl = lin(bbase) @ W, lin(hbase) @ W
q = np.linspace(0, 100, 201)
gain = np.zeros(hl.shape); weight = np.zeros(hl.shape)
for c in REGIONS:
    bsel, hsel = bcov & (bmask[..., c] > 0.5), hcov & (hmask[..., c] > 0.5)
    bq, hq = np.percentile(bl[bsel], q), np.percentile(hl[hsel], q)
    hq = np.maximum.accumulate(hq + np.arange(len(hq)) * 1e-9)       # strictly increasing for interp
    ratio = np.where(hl > 1e-5, np.interp(hl, hq, bq) / np.maximum(hl, 1e-5), 1.0)
    w = np.clip(hmask[..., c], 0, 1) * hcov
    gain += (ratio - 1) * w; weight += w
gain = np.where(weight > 1, gain / np.maximum(weight, 1e-6), gain)    # overlapping mask edges: average the regions
new = np.clip(srgb(np.clip(lin(hbase) * (1 + gain[..., None]), 0, 1)), 0, 1)
after = lin(new) @ W
for c, label in zip(REGIONS, ('hide', 'belly')):
    bsel, hsel = bcov & (bmask[..., c] > 0.5), hcov & (hmask[..., c] > 0.5)
    print(label, 'head lum p10/50/90 before', np.percentile(hl[hsel], [10, 50, 90]).round(3), 'after',
          np.percentile(after[hsel], [10, 50, 90]).round(3), 'body', np.percentile(bl[bsel], [10, 50, 90]).round(3))
buf = io.BytesIO(); Image.fromarray((new * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
tex = mats['DragonHead_A']['pbrMetallicRoughness']['baseColorTexture']['index']
img = doc['textures'][tex]['source']
binary.extend(b'\0' * (-len(binary) % 4))
doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
binary.extend(buf.getvalue())
doc['images'][img] = {'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                      'name': doc['images'][img].get('name', 'head') + '_unified'}
write_glb(dst, doc, bytes(binary))   # the old head image's view stays unreferenced until the reduction compacts it
print('WROTE', dst)
