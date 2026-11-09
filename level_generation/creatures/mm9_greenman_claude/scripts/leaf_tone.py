#!/usr/bin/env python3
"""Body-set leaves toward the head set's leaf tone (mm9_greenman r2): Meshy's full-body paint gave the mantle and kilt
leaves (separate small parts in the body set) a harsh lime/black camouflage pattern, per-channel std 39-46 against the
head retexture's 20-23, so the shoulders read as a different material from the hood. Body leaf texels (loose parts
under 200 triangles, leafparts.py) take a per-channel mean/std transfer onto the head-set leaves' statistics (std x
STD_K), blended by a 1.5 px feathered mask. Reads work/gm_tp_basecolor_graded_orig.png (the grade's output, copied once)
and writes textures/gm_tp_basecolor_graded.png, so a rerun never compounds.
Usage (project folder): leaf_tone.py <export glb> [STD_K 1.15]"""
import os, shutil, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'scripts')
from leafparts import part_labels
glb = sys.argv[1]; K = float(sys.argv[2]) if len(sys.argv) > 2 else 1.15
src = 'work/gm_tp_basecolor_graded_orig.png'
if not os.path.exists(src):
    shutil.copy('textures/gm_tp_basecolor_graded.png', src)
body = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
head = np.asarray(Image.open('textures/gm_tp_head_basecolor.png').convert('RGB')).astype(np.float32)
lb, sb, bigb = part_labels(glb, 'GreenMan', 2048)
lh, sh, bigh = part_labels(glb, 'GreenManHead', 2048)
mb = (lb >= 0) & (lb != bigb) & (sb[np.maximum(lb, 0)] < 200)
# r3: the body shell also carries painted leaves (the chest mantle and the kilt band, a dark-fern camouflage): shell
# texels whose blurred colour is leaf green (G > 1.15 R; the skin is olive-yellow, G/R ~1.05) join the mask
bl = ndimage.gaussian_filter(body, (3, 3, 0))
shell_leaf = (lb == bigb) & (bl[..., 1] > 1.15 * bl[..., 0]) & (bl[..., 1] > 1.6 * bl[..., 2])
shell_leaf = ndimage.binary_opening(shell_leaf, iterations=2)
print('LEAFTONE shell leaf texels', int(shell_leaf.sum()), 'of shell', int((lb == bigb).sum()))
mb = mb | shell_leaf
mh = (lh >= 0) & (lh != bigh) & (sh[np.maximum(lh, 0)] < 200)
hp = head[mh]; g = (hp[:, 1] > hp[:, 0]) & (hp[:, 1] > hp[:, 2])      # green leaves only (not bark, not hands)
mu_h, sd_h = hp[g].mean(0), hp[g].std(0)
bp = body[mb]; mu_b, sd_b = bp.mean(0), bp.std(0)
new = (body - mu_b) / sd_b * (sd_h * K) + mu_h
w = ndimage.gaussian_filter(mb.astype(np.float32), 1.5)[..., None]
out = np.clip(body * (1 - w) + new * w, 0, 255)
Image.fromarray(np.uint8(np.round(out))).save('textures/gm_tp_basecolor_graded.png')
print('LEAFTONE texels', int(mb.sum()), 'body mean/std', mu_b.round(1), sd_b.round(1), '-> head', mu_h.round(1), (sd_h * K).round(1))
