#!/usr/bin/env python3
"""Restore the final hourglass closing plate from its native frame.

The returned hglas120 master shows a full hourglass where the original shows
only the closing plate, so that raw result cannot be fitted faithfully.
"""

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
import torch
from torchvision.transforms import functional

sys.modules['torchvision.transforms.functional_tensor'] = functional
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = REVIEW.parents[2]
WEIGHTS = Path('/tmp/RealESRGAN_x4plus.pth')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cards = json.loads((REVIEW / 'catalog.js').read_text().split('=', 1)[1].strip().removesuffix(';'))['items']
    card = next(item for item in cards if item['name'] == 'hglas120')
    source = (REVIEW / card['original']).resolve()
    native = Image.open(source).convert('RGB')
    pixels = np.asarray(native).astype(np.int16)
    red, blue = pixels[:, :, 0], pixels[:, :, 2]
    subject = (blue < 95) & (red - blue > 20)
    subject = ndimage.binary_fill_holes(ndimage.binary_closing(subject, iterations=1))
    labels, _ = ndimage.label(subject)
    areas = np.bincount(labels.ravel())
    areas[0] = 0
    subject = labels == areas.argmax()
    if subject.mean() < .1 or subject.mean() > .6:
        raise ValueError('Unexpected native closing-plate mask')
    _, nearest = ndimage.distance_transform_edt(~subject, return_indices=True)
    rgb = np.asarray(native)[nearest[0], nearest[1], :3].copy()
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    torch.set_num_threads(8)
    upsampler = RealESRGANer(scale=4, model_path=str(WEIGHTS), model=model,
                            tile=128, tile_pad=10, pre_pad=0, half=False, device='cpu')
    enhanced, _ = upsampler.enhance(rgb[:, :, ::-1].copy(), outscale=4)
    master = Image.fromarray(enhanced[:, :, ::-1], 'RGB').convert('RGBA')
    alpha = Image.fromarray((subject * 255).astype(np.uint8), 'L')
    master.putalpha(alpha.resize(master.size, Image.Resampling.LANCZOS))
    candidate = master.resize(tuple(card['x2_size']), Image.Resampling.LANCZOS)
    master_path = HERE / 'hglas120-master-4x.png'
    candidate_path = HERE / 'candidates' / (card['id'] + '.png')
    master.save(master_path)
    candidate.save(candidate_path)
    (HERE / 'hglas120-repair.json').write_text(json.dumps({
        'source_sha256': card['source_sha256'], 'native_subject_bbox': list(alpha.getbbox()),
        'method': 'RealESRGAN_x4plus on native closing plate with its source-derived alpha',
        'weights_sha256': digest(WEIGHTS), 'master': str(master_path.relative_to(REVIEW)),
        'master_sha256': digest(master_path), 'candidate': str(candidate_path.relative_to(REVIEW)),
        'candidate_sha256': digest(candidate_path), 'candidate_size': list(candidate.size),
        'visual_status': 'pending_manual_review',
    }, indent=2) + '\n')
    print(f'{card["id"]}: native closing plate at {candidate.size}')


if __name__ == '__main__':
    main()
