#!/usr/bin/env python3
"""Texture guard images for mpqem.py (Dwarf copy, Monk paths): Monk_A's base colour in the three tiers, baked from the
shared body paint, the region mask and the tier ramps with the engine rule (as viewer_tiers.py), 1024 px. MonkHead is kept
whole and needs none. -> work/tex_Monk_<variant>.png, work/tex_list.json {material: [files]}"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import tier_textures as TT
TX = HERE.parent / 'mm9_monk_claude' / 'textures'
R = json.load(open(TX / 'mk_ramps.json'))
SRC = {'Monk': 'mk_body_tone.png'}
S = 1024; out = {}
for e in R['materials']:
    base = np.asarray(Image.open(TX / SRC[e['base']]).convert('RGB').resize((S, S), Image.LANCZOS), np.float64) / 255
    mask = np.stack([np.asarray(ch.resize((S, S), Image.BILINEAR), np.float64) / 255 for ch in Image.open(TX / e['mask']).convert('RGBA').split()], -1)
    files = []
    for v in R['variants']:
        f = f"tex_{e['base']}_{v}.png"
        Image.fromarray((np.clip(TT.apply(base, mask, e['ramps'][v]), 0, 1) * 255).astype(np.uint8)).save(HERE / 'work' / f)
        files.append(f)
    out['Monk_A'] = files
json.dump(out, open(HERE / 'work' / 'tex_list.json', 'w'), indent=1); print('TEX', out)
