#!/usr/bin/env python3
"""Review textures per tier (three.js and Blender have no region ramps): the engine rule (viewer_bake.py) on the body,
head and glass base colours with their masks and ramps -> work/tier_<tier>_{body,head,glass}.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from viewer_bake import bake
T = ROOT / 'textures'
load = lambda p, size=None: np.asarray(Image.open(p).convert('RGBA' if 'mask' in p.name else 'RGB').resize(size) if size else Image.open(p).convert('RGBA' if 'mask' in p.name else 'RGB'), np.float64) / 255
body = json.load(open(T / 'hgb_ramps.json')); crest = json.load(open(T / 'hgb_crest_ramps.json'))
for tier in body['variants']:
    for name, base, mask, cfg in (('body', 'hgb_basecolor_1k_graded.png', 'hgb_region_mask_1k.png', body),
                                  ('head', 'hgb_head_basecolor_1k_graded.png', 'hgb_head_region_mask_1k.png', body),
                                  ('glass', 'hgb_glass_basecolor_512.png', 'hgb_glass_mask.png', crest)):
        b = load(T / base)
        m = load(T / mask, b.shape[1::-1])
        ramps = cfg['materials'][0]['ramps'][tier]
        out = bake(b, m, ramps)
        Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(ROOT / f'work/tier_{tier}_{name}.png')
    print('TIER', tier)
