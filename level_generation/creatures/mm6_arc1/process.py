"""Rebuild archer extraction, then apply one fixed family-wide tone grade."""
from pathlib import Path
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'mm6_peasants'))
import process_family

original_extract = process_family.matte.extract


def extract_with_bowstrings(image):
    result, stats = original_extract(image)
    raw = np.array(image.convert('RGB'), dtype=float) / 255
    rgba = np.array(result)
    core = np.minimum(raw[:, :, 0], raw[:, :, 2]) - raw[:, :, 1] <= 8 / 255
    distance = ndimage.distance_transform_edt(~core)
    # The goblin matte's seven-pixel distance cap removes antialiased bowstrings
    # that have no fully opaque core. Recover only strong dark line evidence in
    # those distant pixels; uniform magenta and its faint noise remain excluded.
    selected = ((distance > 6) & (np.maximum(raw[:, :, 0], raw[:, :, 2]) < .88)
                & (raw[:, :, 1] < .25))
    dark_core = core & (raw.max(axis=2) < .3)
    if selected.any() and dark_core.any():
        _, nearest = ndimage.distance_transform_edt(~dark_core, return_indices=True)
        foreground = raw[nearest[0], nearest[1]]
        background = np.array([1., 0., 1.])
        vector = foreground - background
        alpha = np.clip(np.sum((raw - background) * vector, axis=2)
                        / np.maximum(np.sum(vector * vector, axis=2), 1e-8), 0, 1)
        selected &= alpha > rgba[:, :, 3] / 255
        recovered = (raw - (1 - alpha[:, :, None]) * background) / np.maximum(alpha[:, :, None], 1 / 255)
        rgba[:, :, :3][selected] = np.round(np.clip(recovered[selected], 0, 1) * 255).astype(np.uint8)
        rgba[:, :, 3][selected] = np.round(alpha[selected] * 255).astype(np.uint8)
    stats['restored_thin_line_pixels'] = int(selected.sum())
    return Image.fromarray(rgba), stats


def main():
    process_family.matte.extract = extract_with_bowstrings
    process_family.run('arc1')
    # Reviewed native/standing comparison: generated leather, boots and skin were
    # too bright. Fixed gain preserves cross-frame lighting and variant fitting.
    gain = .80
    for directory in ['cleaned', 'aligned_2x']:
        for path in sorted((ROOT / directory).glob('*.png')):
            im = Image.open(path).convert('RGBA')
            pixels = np.array(im)
            pixels[:, :, :3] = np.round(pixels[:, :, :3].astype(float) * gain).astype(np.uint8)
            Image.fromarray(pixels).save(path)
    (ROOT / 'tone.json').write_text(json.dumps(dict(rgb_gain=gain, scope='all base frames, fixed across actions/views',
        reason='Match native dark tonal weight; alpha and mask coverage remain unchanged.',
        actual_generated_sheet_sizes='See generation.json; runtime export is 2x, some source detail is resampled.'),
        indent=2) + '\n')


if __name__ == '__main__':
    main()
