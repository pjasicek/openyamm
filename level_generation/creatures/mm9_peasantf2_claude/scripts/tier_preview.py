#!/usr/bin/env python3
"""Tier body colour previews with the engine's ramp rule (claude_shared/tier_textures.py): textures/preview_body_<variant>.png. Project folder."""
import json, sys
import numpy as np
from PIL import Image
sys.path.insert(0, '../claude_shared')
import tier_textures as TT
R = json.load(open('textures/pf_ramps.json')); e = R['materials'][0]
base = np.asarray(Image.open('textures/pf_body_tone.png').convert('RGB'), np.float64) / 255
mask = np.stack([np.asarray(ch.resize((base.shape[1], base.shape[0]), Image.BILINEAR), np.float64) / 255 for ch in Image.open('textures/' + e['mask']).convert('RGBA').split()], -1)
for v in R['variants']:
    Image.fromarray((np.clip(TT.apply(base, mask, e['ramps'][v]), 0, 1) * 255).astype(np.uint8)).save(f'textures/preview_body_{v}.png'); print('PREVIEW', v)
