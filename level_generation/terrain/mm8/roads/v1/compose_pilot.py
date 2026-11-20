"""Align straight AI road candidates to measured native widths; protect the shared dirt.

Pilot-only outputs: the finished road artwork still needs periodic join repair and review.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
import cv2
from scipy.ndimage import binary_closing, binary_fill_holes, distance_transform_edt, gaussian_filter1d, label, median_filter
from PIL import ImageDraw
from common import *

FOLDER = Path(__file__).resolve().parent


def mask(rgb):
    coverage = (rgb[:, :, 1] / np.maximum(rgb[:, :, 0], 1) > .77) & (rgb[:, :, 2] / np.maximum(rgb[:, :, 0], 1) > .58)
    coverage = binary_closing(np.pad(coverage, 10, mode='edge'), iterations=3)[10:-10, 10:-10]
    components, _ = label(coverage)
    counts = np.bincount(components.ravel()); counts[0] = 0
    coverage = binary_fill_holes(components == counts.argmax())
    # Straight roads are connected strips: dark joints reaching an edge are not
    # narrow slots of earth. Preserve the broad outer contour, not these slots.
    assert np.all(coverage.any(axis=0))
    lower = np.argmax(coverage, axis=0).astype(float)
    upper = 511 - np.argmax(coverage[::-1], axis=0).astype(float)
    lower, upper = [gaussian_filter1d(median_filter(edge, size=11, mode='nearest'), 1)
                    for edge in (lower, upper)]
    return (np.arange(512)[:, None] >= lower) & (np.arange(512)[:, None] <= upper)


def edges(coverage):
    assert np.all(coverage.any(axis=0)), 'Road mask fails to traverse tile'
    return [gaussian_filter1d(a.astype(float), 12) for a in
            (np.argmax(coverage, axis=0), 511 - np.argmax(coverage[::-1], axis=0))]


def main():
    records = []
    sheet = Image.new('RGB', (1024, 560), '#202933'); draw = ImageDraw.Draw(sheet)
    for row, (name, selected) in enumerate((('drsrew', 'drsrew_definition_v3'), ('drsrns', 'drsrns'))):
        original = read(P / 'references' / (name + '.png'), 512)
        generated = read(FOLDER / 'raw' / (selected + '.png'), 512)
        coverage = read(FOLDER / 'inputs' / (name + '_solid_guide.png'))[:, :, 0] > 127
        vertical = name.endswith('ns')
        if vertical:
            original, generated, coverage = original.transpose(1, 0, 2), generated.transpose(1, 0, 2), coverage.T
        old_mask = mask(original); new_mask = mask(generated)
        source_lo, source_hi = edges(new_mask)
        target_lo, target_hi = edges(coverage)
        yy, xx = np.mgrid[:512, :512].astype('float32')
        sample_y = source_lo + (yy - target_lo) * (source_hi - source_lo) / (target_hi - target_lo)
        aligned = cv2.remap(generated.astype('float32'), xx, sample_y.astype('float32'), cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_REFLECT)
        aligned_mask = mask(aligned)
        # Match source stone palette; do not let the generated surrounding earth recolour the master.
        native_stones, ai_stones = original[old_mask], aligned[aligned_mask]
        stone_rgb = (aligned - ai_stones.mean(0)) * np.clip(native_stones.std(0) / np.maximum(ai_stones.std(0), 1), .65, 1.35) + native_stones.mean(0)
        native_earth, ai_earth = original[~old_mask], aligned[~aligned_mask]
        earth_rgb = (aligned - ai_earth.mean(0)) * np.clip(native_earth.std(0) / np.maximum(ai_earth.std(0), 1), .65, 1.35) + native_earth.mean(0)
        inward, outward = distance_transform_edt(aligned_mask), distance_transform_edt(~aligned_mask)
        stone_weight = np.clip((inward - outward + 2) / 4, 0, 1)
        aligned = np.clip(stone_rgb * stone_weight[:, :, None] + earth_rgb * (1 - stone_weight[:, :, None]), 0, 255)
        insertion = np.clip((16 - outward) / 12, 0, 1)
        insertion = insertion * insertion * (3 - 2 * insertion)
        if vertical:
            aligned, insertion, aligned_mask = aligned.transpose(1, 0, 2), insertion.T, aligned_mask.T
        master = read(M / 'materials/dirt.png')
        pixels = seams.srgb(seams.linear(master) * (1 - insertion[:, :, None]) + seams.linear(aligned) * insertion[:, :, None])
        save(FOLDER / 'authoring' / (name + '.png'), pixels)
        save(FOLDER / 'masks' / (name + '.png'), aligned_mask * 255)
        save(FOLDER / 'runtime_pilots' / (name + '.png'), seams.reduce(seams.pad(pixels, 'wrap')))
        assert np.array_equal(pixels[insertion == 0], master[insertion == 0].astype('uint8'))
        records.append(dict(name=name, raw=selected, raw_sha256=sha(FOLDER / 'raw' / (selected + '.png')),
                            mean_native_width=float((target_hi - target_lo).mean()),
                            mean_unaligned_width=float((source_hi - source_lo).mean()),
                            protected_dirt_fraction=float(np.mean(insertion == 0)),
                            runtime_sha256=sha(FOLDER / 'runtime_pilots' / (name + '.png'))))
        for col, path in enumerate((P / 'references' / (name + '.png'), FOLDER / 'raw' / (selected + '.png'),
                                    FOLDER / 'runtime_pilots' / (name + '.png'), FOLDER / 'masks' / (name + '.png'))):
            sheet.paste(Image.open(path).convert('RGB').resize((256, 256)), (col * 256, row * 280 + 24))
            draw.text((col * 256 + 4, row * 280 + 5), name + ' ' + ['original', 'raw AI', 'aligned pilot', 'coverage'][col], fill='white')
    sheet.save(FOLDER / 'pilot_comparison.png')
    (FOLDER / 'pilot_build.json').write_text(json.dumps(dict(status='pilot_only_join_repair_required', tiles=records,
                                                            master_sha256=sha(M / 'materials/dirt.png')), indent=2) + '\n')
    print(json.dumps(records, indent=2))


if __name__ == '__main__':
    main()
