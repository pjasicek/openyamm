#!/usr/bin/env python3
"""Base colour vs every tier with its ramps applied (engine rule, claude_shared/tier_textures.py), crops of the UV
atlas. Usage: tier_preview.py <body> <out.png>"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT
body = sys.argv[1]
R = json.load(open(HERE / 'textures' / f'{body}_ramps.json'))
e = R['materials'][0]
base = np.asarray(Image.open(HERE / 'textures' / f'{body}_basecolor_graded.png').convert('RGB').resize((1024, 1024)),
                  np.float64) / 255
mask = np.stack([np.asarray(ch.resize((1024, 1024), Image.BILINEAR), np.float64) / 255
                 for ch in Image.open(HERE / 'textures' / e['mask']).convert('RGBA').split()], -1)
outs = [base] + [TT.apply(base, mask, e['ramps'][v]) for v in R['variants']]
Image.fromarray((np.clip(np.concatenate(outs, 1), 0, 1) * 255).astype(np.uint8)).resize((512 * len(outs), 512)).save(sys.argv[2])
