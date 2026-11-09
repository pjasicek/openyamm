"""Recover the hat crop and apply only the generated sleeve-opening alpha edits."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
HERE = OUT.parent
sys.path.insert(0, str(HERE / 'review_pass_20260926'))
from repair_assets import clean_spill, fit_native


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def js(path):
    return json.loads(path.read_text().split('=', 1)[1].strip().rstrip(';'))


def main():
    previous = js(OUT / 'previous_review.js')
    catalog = js(HERE / 'catalog.js')
    review = json.loads((OUT / 'review.original.json').read_text())
    operations = {}
    # The generated material/color changes are discarded. Only the opening alpha is used,
    # within these small rectangles in the original 2x canvases; every other pixel is preserved.
    for name, height, regions in [
        ('7item235v2a', 128, [(121, 85, 160, 118)]),
        ('7item236v2a', 192, [(0, 157, 26, 189), (167, 106, 207, 132)]),
    ]:
        asset = catalog['assets'][name]
        old = Image.open(HERE / previous['repairs'][asset['id']]['path']).convert('RGBA')
        generated_path = OUT / 'generated' / (name + '-raw.png')
        generated = Image.open(generated_path).convert('RGBA')
        alpha = np.asarray(generated.getchannel('A').resize((old.width, height), Image.Resampling.LANCZOS))
        source = np.asarray(old)
        result = source.copy()
        region = np.zeros(source.shape[:2], dtype=bool)
        for x, y, right, bottom in regions:
            region[y:bottom, x:right] = True
            result[y:bottom, x:right, 3] = np.minimum(source[y:bottom, x:right, 3], alpha[y:bottom, x:right])
        result[region & (result[:, :, 3] == 0)] = 0
        assert np.array_equal(result[~region], source[~region])
        assert np.all(result[:, :, 3] <= source[:, :, 3])
        fixed = Image.fromarray(result)
        fixed.save(OUT / 'repaired' / (asset['id'] + '.png'))
        operations[name] = {'method': 'imagegen_opening_alpha_only', 'master': str(generated_path.relative_to(HERE)),
            'master_sha256': digest(generated_path), 'prompt': str((generated_path.parent / (name + '-prompt.txt')).relative_to(HERE)),
            'mask_regions_2x': regions, 'changed_alpha_pixels': int((source[:, :, 3] != result[:, :, 3]).sum()),
            'all_pixels_outside_openings_identical': True, 'visible_rgb_unchanged': True}

    name = '6hat1v5'
    asset = catalog['assets'][name]
    raw_path = HERE.parent / 'chat_bundles/remaining_icons_dense_v2_20260922/runs/restore-part-2/v4/sheets/S002/raw.png'
    raw = Image.open(raw_path).convert('RGBA')
    native = Image.open(HERE / asset['native']).convert('RGBA')
    search_box = (1140, 575, 1510, 1042)
    pixels = np.asarray(raw.crop(search_box)).copy()
    labels, count = ndimage.label(pixels[:, :, 3] > 32)
    assert count
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    keep = ndimage.binary_dilation(labels == int(sizes.argmax()), iterations=2)
    pixels[~keep] = 0
    pixels[pixels[:, :, 3] < 16] = 0
    cut = Image.fromarray(pixels)
    cut = cut.crop(cut.getbbox())
    cut.save(OUT / 'generated/6hat1v5-recovered-master.png')
    fixed, cleanup = clean_spill(fit_native(cut, native), native, magenta=True, green=False)
    fixed.save(OUT / 'repaired' / (asset['id'] + '.png'))
    operations[name] = {'method': 'complete_retained_hat_reextraction', 'raw': str(raw_path.relative_to(HERE.parent)),
        'raw_sha256': digest(raw_path), 'raw_search_box': search_box, 'recovered_master_size': cut.size,
        'destination_bbox_2x': [v * 2 for v in native.getbbox()], 'cleanup': cleanup,
        'note': 'Original prepared crop contained no pixels with alpha > 1. Retain genuine green cloth.'}

    repairs = {}
    for name, operation in operations.items():
        asset = catalog['assets'][name]
        target = asset['id']
        old = previous['repairs'].get(target, {'path': asset['candidate'], 'sha256': asset['candidateHash']})
        path = OUT / 'repaired' / (target + '.png')
        compatible = list(dict.fromkeys(old.get('placement_compatible_hashes', []) + [old['sha256'], digest(path)]))
        repairs[target] = {'target': target, 'name': name, 'path': str(path.relative_to(HERE)),
            'sha256': digest(path), 'source_hash': asset['sourceHash'], 'old_sha256': old['sha256'],
            'old_path': old['path'], 'note': review['decisions'][target]['note'], 'operations': [operation],
            'categories': ['openings' if name != '6hat1v5' else 'crop'], 'changed': True,
            'unresolved': [], 'status': 'repair_candidate_needs_review', 'previously_approved': False,
            'placement_compatible_hashes': compatible, 'review_baseline_at': review['exported_at'],
            'pass_id': '20260926_round3'}
    (OUT / 'repairs.json').write_text(json.dumps(repairs, indent=2) + '\n')
    print(json.dumps({name: op for name, op in operations.items()}, indent=2))


if __name__ == '__main__':
    main()
