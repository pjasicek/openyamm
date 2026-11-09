"""Shared sheet budgeting and cheap raw-image screening. Never certifies visual restoration quality."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image


# Retained observations, not service limits or promised delivery sizes. Override with fresh observations.
OBSERVED_ENVELOPES = ((1536, 1024), (1024, 1536), (1254, 1254))


def choose_layout(count, width, height, target=2.2, envelopes=OBSERVED_ENVELOPES):
    if min(count, width, height) <= 0 or not math.isfinite(target) or target < 2:
        raise ValueError('Positive pose/cell sizes and a finite target >=2 are required')
    candidates = []
    for columns in range(1, count + 1):
        rows = math.ceil(count / columns)
        for envelope in envelopes:
            sampling = min(envelope[0] / (columns * width), envelope[1] / (rows * height))
            if sampling >= target:
                candidates.append((sampling, -(columns * rows - count), columns, rows, tuple(envelope)))
    return max(candidates) if candidates else None


def plan(count, width, height, target=2.2, envelopes=OBSERVED_ENVELOPES):
    for poses in range(count, 0, -1):
        chosen = choose_layout(poses, width, height, target, envelopes)
        if chosen:
            sampling, _, columns, rows, envelope = chosen
            return dict(poses=poses, columns=columns, rows=rows, cell_native_size=[width, height],
                        observed_envelope=list(envelope), planned_sampling=sampling,
                        split_required=poses < count, overlap_poses=1 if 1 < poses < count else 0)
    raise ValueError('One complete pose exceeds the observed budget; revise crop or output envelope')


def screen(path, cell, grid, poses, raw_to_native_scale=None):
    width, height = cell
    columns, rows = grid
    if min(width, height, columns, rows, poses) <= 0 or poses > columns * rows:
        raise ValueError('Positive cell/grid sizes and a valid occupied-cell count are required')
    if raw_to_native_scale is not None and (
            not math.isfinite(raw_to_native_scale) or raw_to_native_scale <= 0):
        raise ValueError('Raw-to-native scale must be finite and positive')
    with Image.open(path) as source:
        image = np.asarray(source.convert('RGBA'))
        delivered_size = source.size
    alpha = image[:, :, 3]
    failures, warnings = [], []
    if not np.any(alpha == 0):
        failures.append('No fully transparent background pixels; true transparency required')
    if not np.any(alpha > 0):
        failures.append('Empty artwork')
    nominal = [delivered_size[0] / (columns * width), delivered_size[1] / (rows * height)]
    if min(nominal) < 2:
        failures.append('Delivered grid budget below 2x; replan or verify corrected cell registration')
    borders = np.concatenate([alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1]])
    if np.any(borders > 4):
        warnings.append('Visible outer-border pixels: inspect clipping/background')
    for index in range(columns * rows):
        x, y = index % columns, index // columns
        tile = alpha[y * delivered_size[1] // rows:(y + 1) * delivered_size[1] // rows,
                     x * delivered_size[0] // columns:(x + 1) * delivered_size[0] // columns]
        if index < poses and not np.any(tile > 0):
            failures.append(f'Empty occupied cell {index + 1}')
        elif index >= poses and np.any(tile > 4):
            warnings.append(f'Visible pixels in unused cell {index + 1}: inspect layout/background')
    # Diagnostic only: smooth metal/effects can look flat; noise/sharpening can fool high-frequency metrics.
    rgb = image[:, :, :3].astype(np.float32) / 255
    interior = alpha > 250
    pair_x = interior[:, 1:] & interior[:, :-1]
    pair_y = interior[1:] & interior[:-1]
    count = int(pair_x.sum() + pair_y.sum())
    repeated = int((np.all(rgb[:, 1:] == rgb[:, :-1], axis=2) & pair_x).sum()
                   + (np.all(rgb[1:] == rgb[:-1], axis=2) & pair_y).sum())
    repeat_fraction = repeated / count if count else None
    if repeat_fraction is not None and repeat_fraction > .45:
        warnings.append('Many identical foreground neighbors: inspect enlarged pixel blocks or flat fills')
    sampling = None if raw_to_native_scale is None else 1 / raw_to_native_scale
    if sampling is not None and sampling < 2:
        failures.append('Measured raw-to-native registration below 2x')
    return dict(path=str(path), delivered_size=list(delivered_size), nominal_grid_sampling_xy=nominal,
                actual_registered_sampling=sampling, transparent_pixels=int((alpha == 0).sum()),
                foreground_neighbor_repeat_fraction=repeat_fraction, failures=failures, warnings=warnings,
                status='blocked' if failures else 'static_screen_passed_visual_review_required',
                limits='Grid size is a budget, not anatomical sampling. Alpha does not rule out painted patterns. '
                       'Pixelation, blur, faithful detail, pose and edges require visual inspection at 100%.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    planner = commands.add_parser('plan', help='Maximize whole poses fitting the observed >=2.2x budget')
    planner.add_argument('--poses', type=int, required=True)
    planner.add_argument('--cell', type=int, nargs=2, required=True, metavar=('WIDTH', 'HEIGHT'),
                         help='Padded native sequence-union cell, including any allocated gutters')
    planner.add_argument('--target', type=float, default=2.2)
    planner.add_argument('--envelope', type=int, nargs=2, action='append', help='Observed output size; repeatable')
    checker = commands.add_parser('check', help='Screen a returned PNG; emits no files and never accepts art')
    checker.add_argument('image', type=Path)
    checker.add_argument('--cell', type=int, nargs=2, required=True)
    checker.add_argument('--grid', type=int, nargs=2, required=True, metavar=('COLUMNS', 'ROWS'))
    checker.add_argument('--poses', type=int, required=True)
    checker.add_argument('--raw-to-native-scale', type=float,
                         help='Full measured uniform transform, including all intermediate resizes')
    args = parser.parse_args()
    try:
        if args.command == 'plan':
            result = plan(args.poses, *args.cell, args.target, args.envelope or OBSERVED_ENVELOPES)
        else:
            result = screen(args.image, args.cell, args.grid, args.poses, args.raw_to_native_scale)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return int(bool(result.get('failures')))


if __name__ == '__main__':
    raise SystemExit(main())
