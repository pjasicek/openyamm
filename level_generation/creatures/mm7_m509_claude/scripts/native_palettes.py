#!/usr/bin/env python3
"""Render the original indexed MM7 sprite BMPs through each tier's palette (.act, index 0 transparent) into
references/native_variants/<frame>_<palette>.png. Args: <sprite prefix> <palette> [palette ...]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1] / 'references' / 'native_variants'; OUT.mkdir(parents=True, exist_ok=True)
prefix, pals = sys.argv[1], sys.argv[2:]
for p in pals:
    act = np.frombuffer((ROOT / 'assets_dev/worlds/mm7/textures' / f'pal{int(p):03d}.act').read_bytes()[:768], np.uint8).reshape(256, 3)
    n = 0
    bmps = sorted((ROOT / 'assets_dev/worlds/mm7/sprites').glob(f'{prefix}*.bmp')) or \
        sorted((ROOT / 'assets_dev/engine/sprites').glob(f'{prefix}*.bmp'))          # merged families live in engine/
    for bmp in bmps:
        im = Image.open(bmp)
        assert im.mode == 'P', bmp
        idx = np.asarray(im)
        rgba = np.concatenate([act[idx], np.where(idx == 0, 0, 255).astype(np.uint8)[..., None]], -1)
        Image.fromarray(rgba).save(OUT / f'{bmp.stem}_{p}.png'); n += 1
    print('PALETTE', p, n, 'frames')
