#!/usr/bin/env python3
"""Map post-process of the held-sword retexture pilot (README.md, TEXTURE_QUALITY_PASS.md section 0 step 6).

  python3 post_maps.py resize <icon> <job>     Meshy's 4K maps -> work/<icon>/maps/*_2k.png, one Lanczos downsample
  python3 post_maps.py pack <icon>             after the grade: basecolor.png (graded colour), mr.png and normal.png

pack: metallic is the installed model's metal mask carried onto the new UVs (bake_maps.py oldmetal: Meshy's own
metallic is kept only as variation inside it: metal 0.85-1.0, non-metal 0-0.1), roughness is Meshy's, clamped to
0.12-0.95 on metal. Normal: Meshy's, renormalised after the resize (convention fixed later on the GLB by
tools/normal_map_convention.py). gutter_fill.py runs after this on every map, last.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)


def resize(icon, job):
    src = os.path.join(PROJECT, 'meshy', job)
    maps = os.path.join(PROJECT, 'work', icon, 'maps')
    os.makedirs(maps, exist_ok=True)
    for role in ('base_color', 'metallic', 'roughness', 'normal'):
        image = Image.open(os.path.join(src, f'texture_urls_0_{role}.png'))
        print(role, image.size, image.mode)
        image = image.convert('RGB') if role in ('base_color', 'normal') else image.convert('L')
        if role == 'normal':
            v = np.asarray(image.resize((2048, 2048), Image.LANCZOS), np.float32) / 127.5 - 1.0
            v /= np.maximum(np.linalg.norm(v, axis=2, keepdims=True), 1e-6)
            image = Image.fromarray(np.clip((v + 1.0) * 127.5 + 0.5, 0, 255).astype(np.uint8))
        else:
            image = image.resize((2048, 2048), Image.LANCZOS)
        image.save(os.path.join(maps, f'{role}_2k.png'))


def pack(icon):
    maps = os.path.join(PROJECT, 'work', icon, 'maps')
    graded = os.path.join(maps, 'base_color_2k_graded.png')
    Image.open(graded).convert('RGB').save(os.path.join(maps, 'basecolor.png'))
    metal_mask = Image.open(os.path.join(maps, 'old_metal.png')).convert('L').filter(ImageFilter.GaussianBlur(0.7))
    mask = np.asarray(metal_mask, np.float32) / 255.0
    meshy_metal = np.asarray(Image.open(os.path.join(maps, 'metallic_2k.png')), np.float32) / 255.0
    rough = np.asarray(Image.open(os.path.join(maps, 'roughness_2k.png')), np.float32) / 255.0
    metal = mask * (0.85 + 0.15 * meshy_metal) + (1 - mask) * (0.1 * meshy_metal)
    rough = np.where(mask > 0.5, np.clip(rough, 0.12, 0.95), rough)
    mr = np.stack([np.ones_like(metal), rough, metal], 2)
    Image.fromarray(np.clip(mr * 255 + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(maps, 'mr.png'))
    Image.open(os.path.join(maps, 'normal_2k.png')).save(os.path.join(maps, 'normal.png'))
    on = mask > 0.5
    print('PACK', icon, 'metal share %.2f' % on.mean(), 'meshy metallic on metal p10/p50 %.2f/%.2f' % (
        np.percentile(meshy_metal[on], 10), np.percentile(meshy_metal[on], 50)),
        'roughness on metal p10/p50/p90 %.2f/%.2f/%.2f' % tuple(np.percentile(rough[on], [10, 50, 90])))


if __name__ == '__main__':
    {'resize': lambda: resize(sys.argv[2], sys.argv[3]), 'pack': lambda: pack(sys.argv[2])}[sys.argv[1]]()
