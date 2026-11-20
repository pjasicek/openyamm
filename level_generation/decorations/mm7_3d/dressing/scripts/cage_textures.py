#!/usr/bin/env python3
"""Textures of the MM7 cages (textures/cage_*):
- cage_iron: Poly Haven rusty_metal_04 (CC0; the MM6 fire batch's 1k download, read only), 512: base colour as
  scanned (COLOR_0 tints it to the sprites' dark rusty iron), OpenGL normal, metallic-roughness (G rough, B metal
  from its metal map, halved: the rust is not bare metal).
- cage_prisoner: the MM6 native male creature's atlas (assets_source/worlds/mm6/models/mm6_natm.glb, project art,
  extracted to work/cage_natm_src/), halved to 1040 x 512: base colour, normal, metallic-roughness.
Usage: cage_textures.py"""
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECO = os.path.dirname(os.path.dirname(HERE))
RUST = os.path.join(DECO, 'mm6_dungeons_3d', 'fire', 'source', 'polyhaven', 'rusty_metal_04')
RUST_METAL = os.path.join(DECO, 'mm6_dungeons_3d', 'torch_textures', 'source', 'rusty_metal_04',
                          'rusty_metal_04_metal_1k.png')
NATM = os.path.join(HERE, 'work', 'cage_natm_src')
OUT = os.path.join(HERE, 'textures')


def load(path, size, mode='RGB'):
    return np.asarray(Image.open(path).convert(mode).resize(size, Image.LANCZOS)).astype(np.float32)


def save(array, name):
    Image.fromarray(np.clip(array, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name))
    print('WROTE', name)


os.makedirs(OUT, exist_ok=True)
size = (512, 512)
save(load(os.path.join(RUST, 'rusty_metal_04_diff_1k.png'), size), 'cage_iron_basecolor.png')
save(load(os.path.join(RUST, 'rusty_metal_04_nor_gl_1k.png'), size), 'cage_iron_normal.png')
rough = load(os.path.join(RUST, 'rusty_metal_04_rough_1k.png'), size, 'L')
metal = load(RUST_METAL, size, 'L') * 0.5
save(np.stack([np.zeros_like(rough), rough, metal], -1), 'cage_iron_mr.png')

size = (1040, 512)
save(load(os.path.join(NATM, 'natm_basecolor_1k_head_atlas.png'), size), 'cage_prisoner_basecolor.png')
save(load(os.path.join(NATM, 'natm_normal_1k_head_atlas.png'), size), 'cage_prisoner_normal.png')
save(load(os.path.join(NATM, 'natm_metal_rough_1k_head_atlas.png'), size), 'cage_prisoner_mr.png')
