#!/usr/bin/env python3
"""Grafted head hide vs body hide (user 2026-10-14: "the head graft vs body colour is a bit different"): the region
ramps are shared, but the head's base colour in the hide region was darker and more contrasty (linear luminance
p10/50/90 0.011/0.036/0.106 vs the body's 0.025/0.054/0.094), so every tier's head read deeper. The head hide's
luminance is quantile-matched to the body hide's distribution; each texel is scaled by matched/original luminance
(hue and detail kept), weighted by its hide-mask value. Gold, ivory and eyes are unchanged. Only the head base colour
image changes (shared by the three head tier materials). Usage: unify_head.py <in.glb> <out.glb>"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent)); import glb_raster as G  # noqa: E402
from build_actor_lods import write_glb  # noqa: E402
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
W = np.array([.2126, .7152, .0722])
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = G.read_glb(src); binary = bytearray(binary)
mats = {m['name']: m for m in doc['materials']}
prims = G.lod0_primitives(doc, binary, 'Body')


def load(name):
    m = mats[name]
    base = np.asarray(G.image(doc, binary, m['pbrMetallicRoughness']['baseColorTexture']['index']).convert('RGB'), np.float32) / 255
    mask = np.asarray(G.image(doc, binary, m['extras']['openyamm_region_mask']['index']).convert('RGBA')
                      .resize(base.shape[1::-1], Image.Resampling.BILINEAR), np.float32)[..., 0] / 255
    _, cov = G.raster(prims[name]['pos'], prims[name]['uv'], prims[name]['idx'], base.shape[0])
    return base, mask, cov


bbase, bmask, bcov = load('DrakeBody_A')
hbase, hmask, hcov = load('DrakeHead_A')
bl, hl = lin(bbase) @ W, lin(hbase) @ W
bsel, hsel = bcov & (bmask > 0.5), hcov & (hmask > 0.5)
q = np.linspace(0, 100, 201)
bq, hq = np.percentile(bl[bsel], q), np.percentile(hl[hsel], q)
hq = np.maximum.accumulate(hq + np.arange(len(hq)) * 1e-9)       # strictly increasing for interp
matched = np.interp(hl, hq, bq)
ratio = np.where(hl > 1e-5, matched / np.maximum(hl, 1e-5), 1.0)
w = np.clip(hmask, 0, 1)[..., None] * hcov[..., None]
out = lin(hbase) * (1 + (ratio[..., None] - 1) * w)
new = np.clip(srgb(np.clip(out, 0, 1)), 0, 1)
after = lin(new) @ W
print('head hide lum p10/50/90 before', np.percentile(hl[hsel], [10, 50, 90]).round(3), 'after',
      np.percentile(after[hsel], [10, 50, 90]).round(3), 'body', np.percentile(bl[bsel], [10, 50, 90]).round(3))
buf = io.BytesIO(); Image.fromarray((new * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
tex = mats['DrakeHead_A']['pbrMetallicRoughness']['baseColorTexture']['index']
img = doc['textures'][tex]['source']
binary.extend(b'\0' * (-len(binary) % 4))
doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
binary.extend(buf.getvalue())
doc['images'][img] = {'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                      'name': doc['images'][img].get('name', 'head') + '_unified'}
write_glb(dst, doc, bytes(binary))   # the old head image's view stays unreferenced until the reduction compacts it
print('WROTE', dst)
