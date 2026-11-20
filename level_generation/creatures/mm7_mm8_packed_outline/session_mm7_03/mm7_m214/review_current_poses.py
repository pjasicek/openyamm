"""Prepare original-pixel review pages from the current canonical frame provenance."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

SESSION = Path(__file__).resolve().parent.parent


def prepare(family, selected):
    out = SESSION / family / 'redo_2x'
    registration = json.loads((out / 'registration.json').read_text())
    groups = {}
    for name, entry in registration.items():
        if selected and name not in selected:
            continue
        groups.setdefault((entry['batch'], entry['raw_sha256']), []).append(name)
    evidence = []
    for (batch, digest), names in groups.items():
        for start in range(0, len(names), 2):
            pair = names[start:start + 2]
            images = [Image.open(registration[name]['clean_path']).convert('RGBA') for name in pair]
            page = Image.new('RGB', (sum(im.width * 2 + 24 for im in images),
                                    max(im.height for im in images) + 40), '#242424')
            draw = ImageDraw.Draw(page)
            x = 0
            for name, im in zip(pair, images):
                draw.text((x + 3, 5), name + ' / current 100% delivered pixels / dark + ivory', fill='white')
                page.paste(im, (x, 30), im)
                draw.rectangle((x + im.width + 12, 30, x + im.width * 2 + 11, im.height + 29),
                               fill='#eee6d6')
                page.paste(im, (x + im.width + 12, 30), im)
                x += im.width * 2 + 24
            path = out / 'review' / f'current_{batch}_{start // 2}_100pct.png'
            page.save(path)
            evidence.append(dict(path=str(path.relative_to(out)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                 job='current_' + batch, frames=pair, raw_sha256=digest,
                                 step_indices=[names.index(name) for name in pair]))
    path = out / 'review/resume_detail_100pct.json'
    registry = json.loads(path.read_text())
    replaced = {row['path'] for row in evidence}
    registry['evidence'] = [row for row in registry['evidence'] if row['path'] not in replaced] + evidence
    path.write_text(json.dumps(registry, indent=2) + '\n')
    print(json.dumps(dict(family=family, pages=[row['path'] for row in evidence])), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('families', nargs='+')
    parser.add_argument('--frames', nargs='+')
    args = parser.parse_args()
    for family in args.families:
        prepare(family, args.frames)
