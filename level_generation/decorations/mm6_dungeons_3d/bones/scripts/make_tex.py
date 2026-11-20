#!/usr/bin/env python3
"""Texture set from a Meshy retexture download: textures/<prefix>_basecolor.png, _normal.png and _mr.png (glTF
metallic-roughness: G roughness, B metal), resized to <size> pixels (Lanczos), with optional grades.
Usage: make_tex.py <meshy job dir> <prefix> <size> [--metal-scale k] [--roughness-floor r]"""
import argparse
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parser = argparse.ArgumentParser()
parser.add_argument('job'); parser.add_argument('prefix'); parser.add_argument('size', type=int)
parser.add_argument('--metal-scale', type=float, default=0.0)     # bone is not metal: Meshy's metallic is noise
parser.add_argument('--roughness-floor', type=float, default=0.55)
args = parser.parse_args()
size = (args.size, args.size)
out = os.path.join(HERE, 'textures')
os.makedirs(out, exist_ok=True)


def load(name):
    return Image.open(os.path.join(args.job, f'texture_urls_0_{name}.png'))


base = load('base_color').convert('RGB').resize(size, Image.LANCZOS)
base.save(os.path.join(out, f'{args.prefix}_basecolor.png'))
load('normal').convert('RGB').resize(size, Image.LANCZOS).save(os.path.join(out, f'{args.prefix}_normal.png'))
rough = np.asarray(load('roughness').convert('L').resize(size, Image.LANCZOS), np.float32) / 255
metal = np.asarray(load('metallic').convert('L').resize(size, Image.LANCZOS), np.float32) / 255
rough = np.maximum(rough, args.roughness_floor)
mr = np.zeros(size[::-1] + (3,), np.uint8)
mr[..., 0] = 255
mr[..., 1] = np.round(rough * 255)
mr[..., 2] = np.round(metal * args.metal_scale * 255)
Image.fromarray(mr).save(os.path.join(out, f'{args.prefix}_mr.png'))
print('TEXTURES', args.prefix, size, 'mean base', np.asarray(base).reshape(-1, 3).mean(0).round(1).tolist(),
      'roughness', round(float(rough.mean()), 3))
