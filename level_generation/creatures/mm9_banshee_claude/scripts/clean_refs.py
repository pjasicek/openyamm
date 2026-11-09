#!/usr/bin/env python3
"""True cut-outs of the Codex masters: the returns carry a soft halo in low alpha. Alpha above LOW is the figure, largest component + holes kept; edge feathered one pixel; written as *_clean.png on white-free black-free RGBA.
Usage: clean_refs.py <png> [...] (from the project folder)"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
for f in sys.argv[1:]:
    im = np.asarray(Image.open(f).convert('RGBA')).copy()
    a = im[..., 3].astype(np.float32)
    hist = np.percentile(a[a > 0], [5, 25, 50, 75, 95])
    LOW = 0.72 * np.percentile(a[a > 0], 90)
    m = a > LOW
    m = ndimage.binary_opening(m, iterations=1)
    lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    keep = np.isin(lab, 1 + np.where(sizes > 0.002 * sizes.max())[0])
    keep = ndimage.binary_fill_holes(keep) if '--fill' in sys.argv else keep
    s = ndimage.gaussian_filter(keep.astype(np.float32), 0.8)
    im[..., 3] = (np.clip((s - 0.35) / 0.3, 0, 1) * 255).astype(np.uint8)
    out = Path(f).with_name(Path(f).stem + '_clean.png')
    Image.fromarray(im).save(out)
    print(out, im.shape, 'alpha hist', hist, 'cut', LOW, 'figure', float(keep.mean()), 'parts', int((sizes > 0.002 * sizes.max()).sum()))
