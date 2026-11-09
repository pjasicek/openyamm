#!/usr/bin/env python3
"""Export the selected AI pilot and diagnostic sheets, preserving historical reviews."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', choices=('v2', 'v3_local'),
                        default=json.loads((PROJECT / 'manifest.json').read_text())['selected_version'])
    args = parser.parse_args()
    review = PROJECT / 'review'
    export = PROJECT / 'runtime_x2/6plansky1.png'
    method = 'ImageMagick Lanczos resize to 1024x1024, RGB PNG24; no palette/sharpen/seam edits'
    if args.version == 'v3_local':
        raw = PROJECT / 'generated/v3_offset.png'
        review = review / 'v3'
        review.mkdir(exist_ok=True)
        repaired = review / 'repaired_offset_full.png'
        mask = review / 'repair_mask.png'
        previous = Image.open(PROJECT / 'review/v2/6plansky1.png').convert('RGB')
        offset = Image.open(PROJECT / 'review/restored_offset.png').convert('RGB')
        assert offset.tobytes() == ImageChops.offset(previous, 512, 512).tobytes()
        subprocess.run(['convert', str(raw), '-filter', 'Lanczos', '-resize', '1024x1024!',
                        '-alpha', 'off', 'PNG24:' + str(repaired)], check=True)
        # Restrict the AI result to the reported join. Blur the selection mask only, never the cloud pixels.
        subprocess.run(['convert', '-size', '1024x1024', 'xc:black', '-fill', 'white', '-draw',
                        'rectangle 488,0 535,1023 rectangle 0,488 1023,535', '-blur', '0x12', str(mask)],
                       check=True)
        subprocess.run(['convert', str(PROJECT / 'review/restored_offset.png'), str(repaired), str(mask),
                        '-composite', '-roll', '+512+512', '-alpha', 'off', 'PNG24:' + str(export)], check=True)
        method = ('AI half-offset seam repair, Lanczos to 1024px, local 48px cross selection with sigma-12 '
                  'mask feather, composite onto v2 offset, undo 512px roll; opaque RGB. '
                  'No cloud blur, palette grading, mirrored or forced matching edge strips.')
    else:
        raw = PROJECT / 'generated/v2.png'
        subprocess.run(['convert', str(raw), '-filter', 'Lanczos', '-resize', '1024x1024!',
                        '-alpha', 'off', 'PNG24:' + str(export)], check=True)
    native = Image.open(PROJECT / 'source/6plansky1.png').convert('RGB')
    restored = Image.open(export).convert('RGB')
    assert native.size == (512, 512) and restored.size == (1024, 1024)
    duplicate = Image.open(ROOT / 'assets_dev/worlds/mm6/textures/6sky01.bmp').convert('RGB')
    assert duplicate.size == native.size and duplicate.tobytes() == native.tobytes()
    shutil.copy2(export, PROJECT / 'runtime_x2/6sky01.png')
    metrics = {}
    for name, im in [('native', native), ('restored', restored)]:
        a = np.asarray(im, dtype=np.float32)
        colours, counts = np.unique(np.asarray(im).reshape(-1, 3), axis=0, return_counts=True)
        metrics[name] = {'size': list(im.size), 'mean_rgb': a.mean(axis=(0, 1)).tolist(),
                         'median_rgb': np.median(a, axis=(0, 1)).tolist(),
                         'most_common_rgb': colours[counts.argmax()].tolist(),
                         'wrap_mean_rgb_delta': {
                             'left_right': float(np.abs(a[:, 0] - a[:, -1]).mean()),
                             'top_bottom': float(np.abs(a[0] - a[-1]).mean())}}
        metrics[name]['join_deltas'] = {}
        for axis, delta in [('wrap_lr', a[:, 0] - a[:, -1]), ('wrap_tb', a[0] - a[-1]),
                            ('center_vertical', a[:, im.width // 2] - a[:, im.width // 2 - 1]),
                            ('center_horizontal', a[im.height // 2] - a[im.height // 2 - 1])]:
            delta = np.abs(delta).mean(axis=1)
            metrics[name]['join_deltas'][axis] = {'mean': float(delta.mean()),
                                                 'p95': float(np.percentile(delta, 95)),
                                                 'max': float(delta.max())}
        tile = im.resize((384, 384), Image.Resampling.LANCZOS)
        repeats = Image.new('RGB', (1152, 1152))
        for y in range(3):
            for x in range(3):
                repeats.paste(tile, (x * 384, y * 384))
        repeats.save(review / (name + '_repeat_3x3.png'))
        ImageChops.offset(im, im.width // 2, im.height // 2).save(review / (name + '_offset.png'))
    down = restored.resize(native.size, Image.Resampling.LANCZOS)
    down.save(review / 'restored_native_size.png')
    pair = Image.new('RGB', (1024, 542), '#20232a')
    pair.paste(native, (0, 30))
    pair.paste(down, (512, 30))
    draw = ImageDraw.Draw(pair)
    draw.text((12, 9), 'Native MM6 (512px)', fill='white')
    draw.text((524, 9), 'Restored x2, displayed at native size', fill='white')
    pair.save(review / 'tile_comparison.png')
    metrics['downsample_mean_absolute_rgb_delta'] = float(np.abs(
        np.asarray(native, dtype=np.float32) - np.asarray(down, dtype=np.float32)).mean())
    metrics['files'] = {str(p.relative_to(PROJECT)): digest(p) for p in
                        [PROJECT / 'source/6plansky1.bmp', PROJECT / 'source/6plansky1.png', raw, export]}
    metrics['generated_size'] = list(Image.open(raw).size)
    metrics['export'] = method
    (review / 'asset_checks.json').write_text(json.dumps(metrics, indent=2) + '\n')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
