#!/usr/bin/env python3
"""Fill isolated black specks in the baked AO (PeasantDM4, 2026-11-02): single faces of the puffed sleeves and skirt baked
to AO ~0 inside otherwise open islands (Meshy's folds pinch a face shut), and the gentle grade (AO strength 0.5) turned
them into dark triangular stains on the cloth. Components of AO < LOW smaller than MAXA texels whose surrounding ring
(4 px) is mostly open (mean > RING) take the mean of that ring; large dark islands (interior layers) are kept.
Writes textures/pdm4_tp_ao_2k_fixed.png and review/ao_fix_mask.png. Usage (project folder): ao_fix.py [low 0.25] [floor 0.5]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
LOW = float(sys.argv[1]) if len(sys.argv) > 1 else 0.25
MAXA, RING = 6000, 0.55
ao = np.asarray(Image.open('textures/pdm4_tp_ao_2k.png').convert('L')).astype(float) / 255
dark = ao < LOW
lab, n = ndi.label(dark)
sizes = ndi.sum(dark, lab, range(1, n + 1))
out = ao.copy(); mask = np.zeros_like(dark)
for k in np.nonzero(sizes < MAXA)[0] + 1:
    sl = ndi.find_objects(lab == k)[0] if False else None
objs = ndi.find_objects(lab)
for k, sl in enumerate(objs, 1):
    if sl is None or sizes[k - 1] >= MAXA:
        continue
    y0, y1 = max(sl[0].start - 6, 0), min(sl[0].stop + 6, ao.shape[0]); x0, x1 = max(sl[1].start - 6, 0), min(sl[1].stop + 6, ao.shape[1])
    m = lab[y0:y1, x0:x1] == k
    ring = ndi.binary_dilation(m, iterations=4) & ~m
    vals = ao[y0:y1, x0:x1][ring]
    if len(vals) and vals.mean() > RING and (vals > LOW).mean() > 0.7:
        fill = np.median(vals[vals > LOW])
        mm = ndi.binary_dilation(m, iterations=1)
        out[y0:y1, x0:x1][mm] = np.maximum(out[y0:y1, x0:x1][mm], fill)
        mask[y0:y1, x0:x1] |= mm
# whole islands of outward cloth baked far too dark (the top of the right puffed sleeve under the hair: 0.1-0.3), which
# the grade (AO strength 0.5) turned into dark patches: AO is floored at FLOOR for the grade
FLOOR = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
out = np.maximum(out, FLOOR)
Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255)).save('textures/pdm4_tp_ao_2k_fixed.png')
Image.fromarray(np.uint8(mask) * 255).save('review/ao_fix_mask.png')
print('AO_FIX specks filled', int(ndi.label(mask)[1]), 'texels', int(mask.sum()))
