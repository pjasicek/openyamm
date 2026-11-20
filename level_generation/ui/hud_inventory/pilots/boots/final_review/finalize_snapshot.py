"""Prepare reviewed-tone boots candidates and edge/landmark evidence, without accepting artwork."""
import importlib.util
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
    source_dir, out = HERE / 'assessment_v3', HERE / 'final_review'
    out.mkdir(exist_ok=True)
    process = json.loads((source_dir / 'processing.json').read_text())
    job = next(j for j in read('jobs.json')['jobs'] if j['id'] == 'fitted_equipment_variants-912d78c2f37d')
    targets = {t['id']: t for t in read('expected_targets.json')['targets']}
    edge_tiles = []
    for member in job['members']:
        target = targets[member['target']]
        name = target['runtime_name']
        image = Image.open(source_dir / (name + '.png')).convert('RGBA')
        pixels = np.array(image)
        # One common material grade for all poses, selected against the native leather's median RGB.
        pixels[:, :, :3] = np.round(pixels[:, :, :3].astype(float) * .90).astype('uint8')
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
        record['processing']['final_rgb_multiplier'] = .90
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
        script_sha256=digest(Path(__file__)), rgb_multiplier=.90, status='awaiting_visual_review'), indent=2) + '\n')


if __name__ == '__main__':
    main()
