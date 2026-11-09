#!/usr/bin/env python3
"""Make native-geometry 4x Real-ESRGAN masters for held UI artwork.

These are review candidates, not acceptance or runtime exports. Existing
imagegen returns and canonical checkpoint state are left untouched.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
import torch
from torchvision.transforms import functional

sys.modules['torchvision.transforms.functional_tensor'] = functional

from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HUD = ROOT / 'level_generation/ui/hud_inventory'
sys.path.insert(0, str(HUD))
from freeze_targets import rendered  # noqa: E402

WEIGHTS = Path('/tmp/RealESRGAN_x4plus.pth')
OUTPUT = HERE / 'restored_fallback'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def prepare_rgb(native):
    pixels = np.asarray(native.convert('RGBA'))
    visible = pixels[:, :, 3] > 0
    if not visible.any():
        return None
    _, nearest = distance_transform_edt(~visible, return_indices=True)
    return pixels[nearest[0], nearest[1], :3].copy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--supplement', action='store_true',
                        help='Also process failed retained extractions and the user-flagged slice')
    parser.add_argument('--all-missing', action='store_true',
                        help='Process every still-empty catalog card, including broken reuse promises')
    args = parser.parse_args()
    if not WEIGHTS.is_file():
        raise FileNotFoundError(WEIGHTS)
    catalog = json.loads((HERE / 'catalog.js').read_text().split('=', 1)[1].strip().removesuffix(';'))
    targets = {item['id']: item for item in json.loads((HUD / 'expected_targets.json').read_text())['targets']}
    audits = {item['target_id']: item for item in json.loads(
        (HUD / 'review/second_pass/replacement_audit.json').read_text())['targets']}
    selected = []
    for card in catalog['items']:
        if card['candidates'] or card['raw']:
            continue
        disposition = audits[card['id']]['cells'][0]['disposition']
        if disposition in ('family_quality_hold', 'oversized'):
            selected.append(card['id'])
    if args.supplement:
        report_path = HERE / 'extracted_retained/report.json'
        if report_path.is_file():
            report = json.loads(report_path.read_text())
            selected.extend(key for key, item in report['items'].items() if item['status'] == 'hold')
        selected.extend(card['id'] for card in catalog['items']
                        if card['pipeline_status'] == 'deferred' and card['raw'])
        user_review = json.loads((HERE / 'user_review_2026-09-23.json').read_text())
        selected.extend(key for key, item in user_review['decisions'].items()
                        if item['decision'] == 'flag')
    if args.all_missing:
        selected.extend(card['id'] for card in catalog['items'] if not card['candidates'])
    selected = list(dict.fromkeys(selected))
    selected.sort(key=lambda key: (targets[key]['native_size'][0] * targets[key]['native_size'][1], key))

    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    torch.set_num_threads(8)
    upsampler = RealESRGANer(scale=4, model_path=str(WEIGHTS), model=model,
                            tile=128, tile_pad=10, pre_pad=0, half=False, device='cpu')
    OUTPUT.mkdir(exist_ok=True)
    records = {}
    report_path = OUTPUT / 'manifest.json'
    if report_path.is_file():
        prior = json.loads(report_path.read_text())
        if prior.get('weights_sha256') != digest(WEIGHTS):
            raise ValueError('Existing fallback uses different model weights')
        records = prior['items']
    for number, key in enumerate(selected, 1):
        target = targets[key]
        source = ROOT / target['source_path']
        if digest(source) != target['source_sha256']:
            raise ValueError(f'Stale source: {key}')
        folder = OUTPUT / key
        master_path = folder / 'master-4x.png'
        candidate_path = folder / 'candidate-2x.png'
        old = records.get(key)
        if old and old['source_sha256'] == target['source_sha256'] and master_path.is_file() \
                and candidate_path.is_file() and old['master_sha256'] == digest(master_path) \
                and old['candidate_sha256'] == digest(candidate_path):
            print(f'{number}/{len(selected)} reuse {key}', flush=True)
            continue
        with Image.open(source) as image:
            native = rendered(image, target['compositing']['profiles'][0]).convert('RGBA')
        if native.size != tuple(target['native_size']):
            raise ValueError(f'Wrong native canvas: {key}')
        prepared = prepare_rgb(native)
        if prepared is None:
            master = Image.new('RGBA', (native.width * 4, native.height * 4), (0, 0, 0, 0))
            method = 'deterministic transparent placeholder from empty native art'
        else:
            enhanced, _ = upsampler.enhance(prepared[:, :, ::-1].copy(), outscale=4)
            master = Image.fromarray(enhanced[:, :, ::-1], 'RGB').convert('RGBA')
            alpha = native.getchannel('A').resize(master.size, Image.Resampling.LANCZOS)
            master.putalpha(alpha)
            method = 'RealESRGAN_x4plus native full-canvas inference; original alpha retained'
        candidate = master.resize(tuple(target['x2_size']), Image.Resampling.LANCZOS)
        folder.mkdir(exist_ok=True)
        master.save(master_path)
        candidate.save(candidate_path)
        records[key] = {
            'source_sha256': target['source_sha256'],
            'source_path': target['source_path'],
            'profile': target['compositing']['profiles'][0],
            'native_size': target['native_size'],
            'master_size': list(master.size),
            'candidate_size': list(candidate.size),
            'master': str(master_path.relative_to(HERE)),
            'candidate': str(candidate_path.relative_to(HERE)),
            'master_sha256': digest(master_path),
            'candidate_sha256': digest(candidate_path),
            'method': method,
            'visual_status': 'pending_manual_review',
        }
        report_path.write_text(json.dumps({
            'schema': 1, 'model': 'RealESRGAN_x4plus', 'weights_sha256': digest(WEIGHTS),
            'items': records,
        }, indent=2) + '\n')
        print(f'{number}/{len(selected)} generated {key}', flush=True)


if __name__ == '__main__':
    main()
