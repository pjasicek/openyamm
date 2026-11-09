#!/usr/bin/env python3
"""Preview of a local Phoenix head fix: the Head/Jaw texels of the plumage ramp region (mask 0) are quantile-matched to
the neck's mask-0 luminance; each texel is scaled by matched/original luminance (hue and feather detail kept),
weighted by its mask value. Beak, eyes and mouth (outside mask 0) are unchanged. Writes a GLB with the new base colour."""
import io, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/tools')
from build_actor_lods import read_glb, write_glb  # noqa: E402
P = '/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm8_m572_reduce_claude'
from pathlib import Path
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src); binary = bytearray(binary)
mat = doc['materials'][0]; tex = mat['pbrMetallicRoughness']['baseColorTexture']['index']; img = doc['textures'][tex]['source']
bv = doc['bufferViews'][doc['images'][img]['bufferView']]; s = bv.get('byteOffset', 0)
rgba = np.asarray(Image.open(io.BytesIO(bytes(binary[s:s + bv['byteLength']]))).convert('RGBA'), np.float32) / 255
mi = doc['images'][doc['textures'][mat['extras']['openyamm_region_mask']['index']]['source']]; mv = doc['bufferViews'][mi['bufferView']]; ms = mv.get('byteOffset', 0)
m4 = np.asarray(Image.open(io.BytesIO(bytes(binary[ms:ms + mv['byteLength']]))).convert('RGB'))
H, Wd = rgba.shape[:2]
mask0 = np.asarray(Image.fromarray(m4[..., 0]).resize((Wd, H), Image.Resampling.BILINEAR), np.float32) / 255
d = np.load(f'{P}/work/mesh_in.npz'); fb = np.load(f'{P}/work/src_face_bone.npz'); names = [str(n) for n in fb['names']]
cls = np.array([1 if names[b] in ('Head', 'Jaw') else (2 if names[b].startswith('Neck') else 0) for b in fb['bone']])
lab = Image.new('L', (Wd, H), 0); dr = ImageDraw.Draw(lab); uv = d['wuv'].reshape(-1, 3, 2)
for k in (2, 1):
    for i in np.where(cls == k)[0]:
        dr.polygon([(float(u % 1 * Wd), float((1 - v % 1) * H)) for u, v in uv[i]], fill=k)
lab = np.asarray(lab)
lin = lambda c: np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= .0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - .055)
L = lin(rgba[..., :3]); Y = L @ np.array([.2126, .7152, .0722])
from scipy import ndimage
head = ndimage.binary_dilation(lab == 1, iterations=4) & (lab != 2)
EXTEND = len(sys.argv) > 3 and sys.argv[3] == 'extend'
if EXTEND:
    # brown brow/cere/face texels outside every mask (not the yellow beak, not dark mouth/pupils/hook) join mask 0
    import colorsys
    mfull = np.stack([np.asarray(Image.fromarray(m4[..., k]).resize((Wd, H), Image.Resampling.BILINEAR), np.float32) / 255 for k in range(3)], -1)
    rgb = rgba[..., :3]; mx = rgb.max(2); mn = rgb.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    brown = head & (mfull.max(2) < .5) & (hue >= 5) & (hue <= 45) & (mx >= .12) & (mx < .55) & (sat > .25)
    brown = ndimage.binary_opening(brown, iterations=1)
    print('EXTEND mask0 by', int(brown.sum()), 'texels')
    mask0 = np.maximum(mask0, brown.astype(np.float32))
hsel, nsel = (lab == 1) & (mask0 > .5), (lab == 2) & (mask0 > .5)
q = np.linspace(0, 100, 201); hq, nq = np.percentile(Y[hsel], q), np.percentile(Y[nsel], q)
hq = np.maximum.accumulate(hq + np.arange(len(hq)) * 1e-9)
ratio = np.where(Y > 1e-5, np.interp(Y, hq, nq) / np.maximum(Y, 1e-5), 1.0)
w = mask0 * head
new = L * (1 + (ratio - 1) * w)[..., None]
after = np.clip(new, 0, 1) @ np.array([.2126, .7152, .0722])
print('head mask0 Y p10/50/90 before', np.percentile(Y[hsel], [10, 50, 90]).round(4), 'after', np.percentile(after[hsel], [10, 50, 90]).round(4), 'neck', np.percentile(Y[nsel], [10, 50, 90]).round(4))
out = np.concatenate([np.clip(srgb(np.clip(new, 0, 1)), 0, 1), rgba[..., 3:]], -1)
buf = io.BytesIO(); Image.fromarray((out * 255 + .5).astype(np.uint8)).save(buf, 'PNG')
binary.extend(b'\0' * (-len(binary) % 4))
doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())}); binary.extend(buf.getvalue())
doc['images'][img] = {'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': doc['images'][img].get('name', 'base') + '_head_unified'}
if EXTEND:
    # region mask (1K): channel 0 takes the extended texels (max over each 2x2 block of the 2K map)
    m1 = m4.copy(); ext = (mask0 > .5).reshape(m4.shape[0], Wd // m4.shape[1], m4.shape[1], Wd // m4.shape[1]).max((1, 3))
    m1[..., 0] = np.maximum(m1[..., 0], ext.astype(np.uint8) * 255)
    full = np.asarray(Image.open(io.BytesIO(bytes(binary[ms:ms + mv['byteLength']]))))
    full = full.copy(); full[..., 0] = m1[..., 0]
    mb = io.BytesIO(); Image.fromarray(full).save(mb, 'PNG'); binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(mb.getvalue())}); binary.extend(mb.getvalue())
    k = doc['textures'][mat['extras']['openyamm_region_mask']['index']]['source']
    doc['images'][k] = {'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': doc['images'][k].get('name', 'mask') + '_head_extended'}
write_glb(dst, doc, bytes(binary)); print('WROTE', dst)
