#!/usr/bin/env python3
"""Per-view silhouette IoU of each ladder step against the source (review/ladder/*_sil.png)."""
import sys
import numpy as np
from PIL import Image
for tag in sys.argv[1:]:
    out = []
    for v in ['front', 'back', 'left', 'right', 'q34', 'top', 'atk_left', 'atk_q34', 'dead_q34']:
        a = np.asarray(Image.open(f'review/ladder/source_{v}_sil.png').convert('RGBA'))[..., 3] > 127
        b = np.asarray(Image.open(f'review/ladder/{tag}_{v}_sil.png').convert('RGBA'))[..., 3] > 127
        out.append(f'{v} {(a & b).sum() / (a | b).sum():.4f}')
    print(tag, ' '.join(out))
