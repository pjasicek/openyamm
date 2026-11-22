#!/usr/bin/env python3
"""Carnage Hand texture set from the Meshy retexture (meshy/retexture_v1: 4K paint on our uv_atlas layout from the
four Codex HD masters). Run after scripts/dump_uv3d.py and scripts/bake_ao.py; grade, procedural keep and gutter fill
follow in scripts/build_runtime.sh.

The masters show the mouth closed, so Meshy painted the skin (part 0) and the lip lids (parts 5, 6: red lips) from
them and guessed everything the closed lids hide. Those parts are painted here (clean.py part ids):
  1 rim     the strip from the cut to the aperture: Meshy's skin outside, blending into dark red gum at the aperture
  2 gullet  dark red at the rim to nearly black 8 cm down, Meshy's luminance detail kept on top (x0.8..1.2)
  3 tongue  red-pink, lighter where it faces out of the palm
  4 fangs   grey-silver (the native sprite's fangs), darker at the root, light toward the tip
Writes into textures/:
  hand_basecolor.png          2K base colour (4K paint downsampled once, Lanczos)
  hand_normal_1k.png          Meshy normal (+y down; tools/prepare_actor_glb.py converts it); flat on fangs and tongue
  hand_mr_1k.png              ORM: R baked AO (1 on the procedural mouth parts), G roughness, B 0
  hand_region_mask.png        1K RGBA: R skin (part 0), G maw (rim, gullet, tongue, lips), B fangs; padded
  hand_material_classes.png   1K labels: 1 skin, 7 mouth interior (rim, gullet, tongue, lips), 5 fangs
and work/part_map_2k.npy (for keep_procedural.py)."""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C   # noqa: E402  (rasterise: 2048 part/xyz maps)

SRC = ROOT / 'meshy/retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'
N = 2048
data = np.load(ROOT / 'work/uv3d.npz')
tri_map, xyz = C.rasterise(data, values=np.arange(len(data['part'])))
valid = tri_map >= 0
part = np.where(valid, data['part'][np.maximum(tri_map, 0)], -1)
nrm = data['normal'][np.maximum(tri_map, 0)]
M = json.load(open(ROOT / 'work/mouth.json'))
O, n, U, V = (np.array(M[k]) for k in ('O', 'n', 'U', 'V'))
AA, AB = M['aperture']; h0 = M['h0']
d = xyz - O
du, dv, dn = d @ U, d @ V, d @ n
re = np.sqrt((du / AA) ** 2 + (dv / AB) ** 2)


def save(array, path, size=None, mode=None):
    image = Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8), mode)
    if size:
        image = image.resize((size, size), Image.LANCZOS)
    image.save(path, optimize=True)


base = np.asarray(Image.open(f'{SRC}_base_color.png').convert('RGB').resize((N, N), Image.LANCZOS), np.float32) / 255
lum = base @ np.array([0.299, 0.587, 0.114], np.float32)
detail = np.clip(lum / np.maximum(ndimage.gaussian_filter(lum, 6), 1e-3), 0.8, 1.2)[..., None]
skin = valid & (part == 0)
print('SKIN paint median', np.round(np.median(base[skin], 0) * 255).tolist())
# skin brightness: the paint median (170, 112, 71) sits on the sprite's median (180, 112, 68), which carries baked
# shading; x1.15 brings it to the Flying Feet's accepted skin (same palette, paint median 210, 141, 94) before the AO
# grade darkens the creases again
SKIN_GAIN = 1.15
base = np.where((skin | (part == 1))[..., None], np.clip(base * SKIN_GAIN, 0, 1), base)
gum = np.array([0.42, 0.06, 0.06]); deep = np.array([0.07, 0.01, 0.01])
# rim: skin paint outside -> gum at the aperture
rim = part == 1
w = np.clip((1.32 - re) / 0.28, 0, 1)[..., None]
base = np.where(rim[..., None], base * (1 - w) + gum * detail * w, base)
# gullet: gum at the rim, nearly black at the bottom
gul = part == 2
t = np.clip((h0 - dn) / 0.08, 0, 1)[..., None] ** 0.7
base = np.where(gul[..., None], (gum + (deep - gum) * t) * detail, base)
# tongue
ton = part == 3
face = np.clip(nrm @ n, 0, 1)[..., None]
base = np.where(ton[..., None], np.array([0.42, 0.07, 0.09]) + np.array([0.33, 0.12, 0.12]) * face, base)
# fangs: root grey -> light silver tip (re 0.985 at the root on the rim, smaller toward the tip)
fang = part == 4
ft = np.clip((0.99 - re) / 0.35, 0, 1)[..., None]
base = np.where(fang[..., None], np.array([0.40, 0.38, 0.37]) + np.array([0.42, 0.43, 0.43]) * ft, base)
save(base, OUT / 'hand_basecolor.png')

flat = fang | ton
normal = np.asarray(Image.open(f'{SRC}_normal.png').convert('RGB').resize((N, N), Image.LANCZOS), np.float32) / 255
normal = np.where(flat[..., None], np.array([0.5, 0.5, 1.0], np.float32), normal)
save(normal, OUT / 'hand_normal_1k.png', 1024)
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((N, N), Image.LANCZOS), np.float32) / 255
ao = np.asarray(Image.open(OUT / 'hand_ao_2k.png').convert('L'), np.float32) / 255
print('ROUGHNESS skin p10/p50/p90', np.round(np.percentile(rough[skin], [10, 50, 90]), 3).tolist())
rough = np.clip(rough, 0.45, 0.9)
rough = np.where(fang, 0.35, np.where(ton | gul, 0.4, rough))
proc = fang | ton | gul | rim
ao = np.where(proc, 1.0, ao)
save(np.stack([ao, rough, np.zeros_like(ao)], -1), OUT / 'hand_mr_1k.png', 1024)

maw = valid & np.isin(part, (1, 2, 3, 5, 6))
chan = np.zeros((N, N, 4), np.float32)
chan[..., 0] = skin; chan[..., 1] = maw; chan[..., 2] = fang
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
padded = chan[iy, ix]; padded[valid] = chan[valid]
for c in range(3):
    padded[..., c] = np.where(valid, ndimage.gaussian_filter(padded[..., c], 0.7), padded[..., c])
chans = [Image.fromarray((padded[..., c] * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
         for c in range(4)]
Image.merge('RGBA', chans).save(OUT / 'hand_region_mask.png')
classes = np.zeros((N, N), np.uint8)
classes[skin] = 1; classes[maw] = 7; classes[fang] = 5
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'hand_material_classes.png')
np.save(ROOT / 'work/part_map_2k.npy', part.astype(np.int8))
print('COMPOSED skin', int(skin.sum()), 'maw', int(maw.sum()), 'fangs', int(fang.sum()))
