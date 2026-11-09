"""Arrange existing, unscaled palette/pose evidence for session-local visual review."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

SESSION = Path(__file__).resolve().parent.parent


def group(family):
    root = SESSION / family
    assert not (root / 'review/acceptance.json').exists(), 'Accepted family is frozen'
    checks = json.loads((root / 'review/palette_checks.json').read_text())
    paths = sorted((root / 'review').glob('palette_pose_*.png'))
    registration = json.loads((root / 'registration.json').read_text())
    paths = [p for p in paths if p.stem.removeprefix('palette_pose_') in registration]
    records = []
    for start in range(0, len(paths), 4):
        selected = paths[start:start + 4]
        images = [Image.open(p).convert('RGB') for p in selected]
        width = max(im.width for im in images)
        height = max(im.height for im in images) + 22
        canvas = Image.new('RGB', (width * 2, height * 2), '#242626')
        draw = ImageDraw.Draw(canvas)
        for i, (p, im) in enumerate(zip(selected, images, strict=True)):
            x, y = i % 2 * width, i // 2 * height
            draw.text((x + 4, y + 4), p.stem.removeprefix('palette_pose_'), fill='white')
            canvas.paste(im, (x, y + 22))
        target = root / 'review' / f'palette_group_{start // 4:02}.png'
        canvas.save(target)
        records.append(dict(path=str(target), sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                            source_paths=[str(p) for p in selected],
                            frames=[p.stem.removeprefix('palette_pose_') for p in selected],
                            size=list(canvas.size), unscaled=True))
    (root / 'review/palette_groups.json').write_text(json.dumps(dict(
        status='visual_review_pending', frames=len(paths), palettes=checks['palettes'],
        evidence=records, method='Unscaled 100% physical masters, native NN 2x and R8 masks, '
                                 'arranged in 2x2 pose groups; every native palette is retained'), indent=2) + '\n')
    print(f'{family}: {len(paths)} poses in {len(records)} unscaled palette groups')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family')
    group(parser.parse_args().family)
