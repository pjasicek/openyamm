"""Reproduce the full-canvas Air restoration and measure interior alignment; never auto-approve."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import signal

HERE = Path(__file__).resolve().parent
HUD = HERE.parents[1]
sys.path.insert(0, str(HUD))
from finalize_classification import ROOT, digest, read
import registration

PATCHES = {
    'air_title': (190, 75, 90, 30),
    'lower_wind_face': (145, 161, 104, 58),
    'upper_wind_face': (150, 105, 78, 64),
    'left_corner': (80, 15, 35, 60),
    'right_corner': (1140, 15, 35, 60),
    'center_bottom': (606, 908, 50, 40),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert not out.exists(), 'Use a fresh directory to preserve existing review evidence'
    out.mkdir(parents=True)
    raw = HUD / 'checkpoint/attempts/af21a026307e489181c7f2604ddbdc87/raw.png'
    member = next(j for j in read('jobs.json')['jobs'] if j['id'] == 'spellbook_page-928106ac2fea')['members'][0]
    target = next(t for t in read('expected_targets.json')['targets'] if t['id'] == member['target'])
    image = Image.open(raw).convert('RGB').resize((1280, 960), Image.Resampling.LANCZOS)
    artifact = out / 'sba000.png'
    image.save(artifact)
    result = registration.evidence(member, target, artifact, out / 'registration')
    native = Image.open(ROOT / member['source_path']).convert('RGB').resize(image.size, Image.Resampling.BICUBIC)
    n, r = [np.asarray(i.convert('L'), dtype=float) for i in (native, image)]
    landmarks, matches = [], []
    detail = Image.new('RGB', (900, 600), '#333333')
    draw = ImageDraw.Draw(detail)
    for index, (name, (x, y, w, h)) in enumerate(PATCHES.items()):
        template = n[y:y + h, x:x + w]
        search = r[y - 8:y + h + 8, x - 8:x + w + 8]
        z, ones = template - template.mean(), np.ones(template.shape)
        scores = signal.correlate2d(search, z, mode='valid')
        total = signal.correlate2d(search, ones, mode='valid')
        squares = signal.correlate2d(search * search, ones, mode='valid')
        scores /= np.sqrt(np.maximum(squares - total * total / template.size, 1e-10) * (z * z).sum())
        iy, ix = np.unravel_index(np.argmax(scores), scores.shape)
        dx, dy = int(ix) - 8, int(iy) - 8
        landmarks.append(dict(name=name, source_xy=[(x + w / 2) / 2, (y + h / 2) / 2],
                              restored_xy=[x + w / 2 + dx, y + h / 2 + dy]))
        matches.append(dict(name=name, reference_patch_x2=[x, y, w, h], search_radius_x2=8,
                            measured_shift_x2=[dx, dy], normalized_correlation=float(scores[iy, ix])))
        tx, ty = index % 3 * 300, index // 3 * 300
        draw.text((tx, ty), name + ': native / restored', fill='white')
        for row, source in enumerate((native, image)):
            crop = source.crop((x - 6, y - 6, x + w + 6, y + h + 6))
            crop.thumbnail((280, 120))
            detail.paste(crop, (tx, ty + 24 + row * 135))
    detail.save(out / 'landmark-details.png')
    record_path = Path(result['registration_record'])
    record = json.loads(record_path.read_text())
    record.update(landmarks=landmarks, patch_matches=matches,
                  landmark_method='Local normalized correlation of native bicubic x2 grayscale patches; inspect visually')
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    (out / 'process_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (out / 'processing.json').write_text(json.dumps(dict(raw=str(raw), raw_sha256=digest(raw),
        script_sha256=digest(Path(__file__)), resize='whole RGB canvas to 1280x960, LANCZOS; no crop or grade',
        artifact_sha256=digest(artifact), status='awaiting_visual_review'), indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
