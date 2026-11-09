"""Session-only complete returned-pose evidence, keeping delivered pixels at 100%."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path.cwd().resolve()
SESSION = REPO / 'level_generation/creatures/mm7_mm8_packed_outline/session_mm7_03'


def review(family, jobs):
    out = SESSION / family / 'redo_2x'
    evidence = []
    for job in jobs:
        report_path = out / 'review' / (job + '_extraction.json')
        if not report_path.exists():
            continue
        report = json.loads(report_path.read_text())
        frames = report['frames']
        for start in range(0, len(frames), 2):
            selected = frames[start:start + 2]
            images = [Image.open(REPO / f['clean_path']).convert('RGBA') for f in selected]
            widths = [im.width * 2 + 24 for im in images]
            page = Image.new('RGB', (sum(widths), max(im.height for im in images) + 40), '#242424')
            draw = ImageDraw.Draw(page)
            x = 0
            for frame, im, width in zip(selected, images, widths):
                draw.text((x + 3, 5), frame['frame'] + ' / 100% delivered pixels / dark + ivory', fill='white')
                page.paste(im, (x, 30), im)
                draw.rectangle((x + im.width + 12, 30, x + im.width * 2 + 11, im.height + 29), fill='#eee6d6')
                page.paste(im, (x + im.width + 12, 30), im)
                x += width
            path = out / 'review' / (job + '_detail_100pct_' + str(start // 2) + '.png')
            page.save(path)
            evidence.append(dict(path=str(path.relative_to(out)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                 job=job, step_indices=list(range(start, start + len(selected))),
                                 frames=[f['frame'] for f in selected], raw_sha256=report['raw_sha256']))
    record = out / 'review' / 'resume_detail_100pct.json'
    previous = json.loads(record.read_text()) if record.exists() else dict(evidence=[])
    replaced = {row['job'] for row in evidence}
    previous['evidence'] = [row for row in previous['evidence'] if row['job'] not in replaced] + evidence
    previous['status'] = 'visual_review_pending'
    record.write_text(json.dumps(previous, indent=2) + '\n')
    print(json.dumps(dict(family=family, pages=[row['path'] for row in evidence])), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('families', nargs='+')
    parser.add_argument('--jobs', nargs='+', required=True)
    args = parser.parse_args()
    for family in args.families:
        review(family, args.jobs)
