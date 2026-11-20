"""Keep mask for the PeasantF3 follow-up compose (2026-11-11): the re-rendered sari (mfp_sari.py mask), the blouse
region and the flat body skin (round2_textures.py paints skin one colour, 146/85/56 in sRGB, without baked light: the 4K paint's skin
detail drew the collarbone spots). Also writes <approved-with-sari prefix>_* (the sari composite as basecolor, the
approved region mask, normal, metal/roughness and raster copied) for tp_compose.py.

Usage: mfp_keep_mask.py <approved prefix> <sari prefix> <out keep png> <out approved prefix>"""
import shutil
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

approved, sari, out_keep, out_appr = sys.argv[1:5]
a = np.asarray(Image.open(f'{approved}_basecolor.png').convert('RGB'), np.int32)
cov = np.load(f'{approved}_raster2048.npz')['tri_id'] >= 0
skin_rgb = np.array([146, 85, 56])
dist = np.abs(a - skin_rgb).max(-1)
skin = cov & (dist <= 6)
skin = ndimage.binary_opening(skin, iterations=1)
skin = cov & (skin | (ndimage.binary_dilation(skin, iterations=1) & (dist <= 15)))
sari_mask = np.asarray(Image.open(f'{sari}_sari_mask.png')) > 127
# blouse (region mask channel 0, ramped per tier): a procedural weave in production; the paint's detail pushed its
# luminance past the ramp's white top entry along the neckline (pale stipple), so it keeps the approved colour too
region = np.asarray(Image.open(f'{approved}_region_mask.png').convert('RGBA'))[..., 0] > 8
blouse = cov & ndimage.binary_dilation(region, iterations=2)
keep = (skin | sari_mask | blouse) & cov
Image.fromarray((keep * 255).astype(np.uint8)).save(out_keep)
print(f'skin {skin.sum()} sari {sari_mask.sum()} blouse {blouse.sum()} keep {keep.sum()} of {cov.sum()} covered ({keep.sum() / cov.sum():.1%})')
shutil.copyfile(f'{sari}_sari.png', f'{out_appr}_basecolor.png')
for kind in ('region_mask', 'normal', 'metal_rough'):
    shutil.copyfile(f'{approved}_{kind}.png', f'{out_appr}_{kind}.png')
shutil.copyfile(f'{approved}_raster2048.npz', f'{out_appr}_raster2048.npz')
