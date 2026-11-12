#!/usr/bin/env python3
"""Copy the 2026-10-06 Codex masters (mm8_m400/3d_20261006/references, generated from the native m400 bitmaps,
gray studio background) as references_hd/00-04 and write *_clean.png with true alpha: the background is flood-filled
from the border (colour within TOL of the border median), then the matte is eroded by 1 px and feathered."""
import hashlib, json, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]; SRC = HERE.parent / 'mm8_m400/3d_20261006/references'
MAP = {'00_three_quarter': 'threequarter_v2_open_hands', '01_front': 'front_v1', '02_back': 'back_v1',
       '03_left': 'left_v1', '04_right': 'right_v1'}
TOL = 14
out = HERE / 'references_hd'; rec = []
for dst, src in MAP.items():
    shutil.copy(SRC / f'{src}.png', out / f'{dst}.png')
    im = np.asarray(Image.open(SRC / f'{src}.png').convert('RGB')).astype(int)
    border = np.concatenate([im[0], im[-1], im[:, 0], im[:, -1]])
    bg = np.median(border, 0)
    close = np.abs(im - bg).max(-1) <= TOL
    lab, _ = ndimage.label(close)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    back = np.isin(lab, list(edge))
    fg = ndimage.binary_fill_holes(~back)
    fg = ndimage.binary_erosion(fg, iterations=1)
    alpha = ndimage.gaussian_filter(fg.astype(float), 0.7)
    rgba = np.dstack([im, np.round(alpha * 255)]).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(out / f'{dst}_clean.png')
    rec.append({'view': dst, 'source': str((SRC / f'{src}.png').relative_to(HERE.parents[2])),
                'sha256': hashlib.sha256((SRC / f'{src}.png').read_bytes()).hexdigest(), 'bg': bg.tolist(),
                'clean_sha256': hashlib.sha256((out / f'{dst}_clean.png').read_bytes()).hexdigest(),
                'foreground_px': int(fg.sum())})
json.dump({'note': 'Reused gated masters of the 2026-10-06 run (playbook quick start 0: an earlier attempt\'s masters '
           'may be reused); prompts in the source folder; *_clean = alpha matte by clean_masters.py', 'views': rec},
          open(out / 'generation_runs.json', 'w'), indent=1)
print('MASTERS', [(r['view'], r['foreground_px']) for r in rec])
