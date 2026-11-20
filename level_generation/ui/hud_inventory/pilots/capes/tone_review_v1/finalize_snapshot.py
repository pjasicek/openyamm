"""Prepare reviewed-tone boots candidates and edge/landmark evidence, without accepting artwork."""
import importlib.util
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
HUD = HERE.parents[1]
sys.path.insert(0, str(HUD))
from finalize_classification import ROOT, digest, read
from freeze_targets import rendered
import registration


def components(image):
    labels, count = ndimage.label(np.array(image.getchannel('A')) >= 128)
    results = []
    for i in range(1, count + 1):
        y, x = np.nonzero(labels == i)
        if len(x) < 50:
            continue
        results.append(dict(bounds=[int(x.min()), int(y.min()), int(x.max() + 1), int(y.max() + 1)],
            cuff_apex=[float(np.median(x[y == y.min()])), int(y.min())],
            toe_extreme=[int(x.min()), float(np.median(y[x == x.min()]))]))
    return sorted(results, key=lambda c: c['bounds'][0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default='assessment_v3')
    parser.add_argument('--output', default='final_review')
    parser.add_argument('--job', default='fitted_equipment_variants-912d78c2f37d')
    parser.add_argument('--rgb-gain', type=float, nargs=3, default=[.9, .9, .9])
    parser.add_argument('--rgb-offset', type=float, nargs=3, default=[0, 0, 0])
    parser.add_argument('--cell-shifts', type=json.loads, default={},
                        help='Measured whole-pair XY translations, keyed by runtime name')
    parser.add_argument('--repair-contour-spill', action='store_true')
    args = parser.parse_args()
    source_dir, out = HERE / args.source, HERE / args.output
    out.mkdir(exist_ok=False)
    process = json.loads((source_dir / 'processing.json').read_text())
    job = next(j for j in read('jobs.json')['jobs'] if j['id'] == args.job)
    targets = {t['id']: t for t in read('expected_targets.json')['targets']}
    edge_tiles = []
    for member in job['members']:
        target = targets[member['target']]
        name = target['runtime_name']
        image = Image.open(source_dir / (name + '.png')).convert('RGBA')
        shift = args.cell_shifts.get(name, [0, 0])
        if shift != [0, 0]:
            image = image.convert('RGBa').transform(image.size, Image.Transform.AFFINE,
                (1, 0, -shift[0], 0, 1, -shift[1]), Image.Resampling.BICUBIC).convert('RGBA')
        pixels = np.array(image)
        repaired = 0
        if args.repair_contour_spill:
            rgb = pixels[:, :, :3].astype(float)
            contour = (pixels[:, :, 3] > 0) & (ndimage.distance_transform_edt(pixels[:, :, 3] >= 128) <= 4)
            excess = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1] - 2)
            repair = contour & (excess > 0)
            rgb[:, :, 0][repair] -= excess[repair]
            rgb[:, :, 2][repair] -= excess[repair]
            pixels[:, :, :3] = np.clip(rgb, 0, 255).astype('uint8')
            repaired = int(repair.sum())
        # One recorded common material grade for all poses, selected against the native references.
        pixels[:, :, :3] = np.clip(np.round(pixels[:, :, :3].astype(float) * args.rgb_gain
                                           + args.rgb_offset), 0, 255).astype('uint8')
        image = Image.fromarray(pixels)
        artifact = out / (name + '.png')
        image.save(artifact)
        result = registration.evidence(member, target, artifact, out / 'registration')
        native = rendered(Image.open(ROOT / member['source_path']), 'item').resize(
            image.size, Image.Resampling.NEAREST)
        native_parts, restored_parts = components(native), components(image)
        assert len(native_parts) == len(restored_parts)
        record_path = Path(result['registration_record'])
        record = json.loads(record_path.read_text())
        record['processing'] = next(r for r in process['cells'] if r['cell'] == member['id'])
        record['processing']['final_rgb_gain'] = args.rgb_gain
        record['processing']['final_rgb_offset'] = args.rgb_offset
        record['processing']['final_pair_shift_xy'] = shift
        record['processing']['repaired_contour_pixels'] = repaired
        record['component_measurements'] = dict(native_x2=native_parts, restored_x2=restored_parts)
        # These are actual detected contour feature coordinates, not copied expected output coordinates.
        # They remain unapproved until the comparison is inspected and visual_fit_notes is filled in.
        record['landmarks'] = [dict(name=f'boot_{i + 1}_{feature}',
            source_xy=[v / 2 for v in n[feature]], restored_xy=r[feature])
            for i, (n, r) in enumerate(zip(native_parts, restored_parts))
            for feature in ['cuff_apex', 'toe_extreme']]
        record_path.write_text(json.dumps(record, indent=2) + '\n')
        # Full enlarged light/dark images expose thin contours and internal details together.
        for label, picture in [('native', native), ('restored', image)]:
            for color in ['#eeeeee', '#171717']:
                tile = Image.new('RGBA', picture.size, color)
                tile.alpha_composite(picture)
                edge_tiles.append((name + ' ' + label + ' ' + color,
                                   tile.convert('RGB').resize((picture.width * 3, picture.height * 3),
                                                             Image.Resampling.NEAREST)))
    width = max(t.width for _, t in edge_tiles)
    height = max(t.height for _, t in edge_tiles) + 24
    for index in range(4):
        contact = Image.new('RGB', (width * 2, height * 2), '#666666')
        draw = ImageDraw.Draw(contact)
        for col, (label, tile) in enumerate(edge_tiles[index * 4:index * 4 + 4]):
            x, y = (col % 2) * width, (col // 2) * height
            draw.text((x, y), label, fill='white')
            contact.paste(tile, (x, y + 24))
        contact.save(out / f'edges-{index + 1}.png')
    (out / 'finalize_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (out / 'processing.json').write_text(json.dumps(dict(parent_processing_sha256=digest(source_dir / 'processing.json'),
        script_sha256=digest(Path(__file__)), rgb_gain=args.rgb_gain, rgb_offset=args.rgb_offset,
        command=sys.argv, status='awaiting_visual_review'), indent=2) + '\n')


if __name__ == '__main__':
    main()
