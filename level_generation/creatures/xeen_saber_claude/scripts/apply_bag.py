#!/usr/bin/env python3
"""Put the mouth bag's own paint (work/bag_paint.npz from compose_saber.py) back into the graded base colour: the
grade's ambient occlusion would turn the cavity inside the head almost black. Usage: apply_bag.py <graded png>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
d = np.load(ROOT / 'work/bag_paint.npz')
p = Path(sys.argv[1]); im = np.asarray(Image.open(p).convert('RGB')).copy()
im[d['mask']] = (d['rgb'] * 255 + 0.5).astype(np.uint8)
Image.fromarray(im).save(p)
print('BAG texels', int(d['mask'].sum()))
