#!/usr/bin/env python3
"""Identical-camera review-viewer shots for a texture quality pass: the shots of tools/run_creature_review.py (same
viewer, same capture script) with free cameras for close-ups, every tier.

  texpass_viewer_shots.py shots <project> <out dir> <tier id,...> name:clip:time:view:focus[:cx,cy,cz:tx,ty,tz] ...
      writes <out dir>/<tier>_<name>.png (glTF Y-up metres, the viewer's frame; the wrapper accepts presets only).
  texpass_viewer_shots.py sheet <out.png> <before dir> <after dir> <tier id,...> <name,...> [crop height]
      rows = shots, columns = before | after per tier, labelled.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / 'level_generation/creatures/mm8_m424_claude/scripts/viewer_shots.mjs'


def shots(project, out, tiers, specs):
    project = Path(project).resolve()
    viewer = project / 'review/viewer'
    base = f'http://127.0.0.1:8912/{viewer.relative_to(REPO).as_posix()}/'
    tmp = Path(out) / '_tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    for tier in tiers.split(','):
        result = subprocess.run(['node', str(SCRIPT), f'{base}?model={tier}', str(tmp), *specs], cwd=REPO, text=True,
                                capture_output=True)
        print(tier, result.stdout.strip(), result.stderr.strip()[-300:])
        if result.returncode:
            raise SystemExit(result.returncode)
        for spec in specs:
            name = spec.split(':')[0]
            (tmp / f'{name}.png').replace(Path(out) / f'{tier}_{name}.png')
    tmp.rmdir()


def sheet(out, before, after, tiers, names, height=None):
    from PIL import Image, ImageDraw
    tiers, names = tiers.split(','), names.split(',')
    first = Image.open(Path(before) / f'{tiers[0]}_{names[0]}.png')
    w, h = first.width, height or first.height
    scale = 0.5
    cw, ch = int(w * scale), int(h * scale)
    canvas = Image.new('RGB', (cw * 2 * len(tiers), (ch + 18) * len(names)), (24, 26, 30))
    draw = ImageDraw.Draw(canvas)
    for r, name in enumerate(names):
        for t, tier in enumerate(tiers):
            for k, (label, folder) in enumerate((('before', before), ('after', after))):
                im = Image.open(Path(folder) / f'{tier}_{name}.png').convert('RGB').crop((0, 24, w, 24 + h - 60))
                x, y = (t * 2 + k) * cw, r * (ch + 18)
                canvas.paste(im.resize((cw, int((h - 60) * scale))), (x, y + 18))
                draw.text((x + 4, y + 3), f'{tier} {name} {label}', fill=(235, 235, 235))
    canvas.save(out)
    print('SHEET', out, canvas.size)


if __name__ == '__main__':
    if sys.argv[1] == 'shots':
        shots(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
    else:
        sheet(*sys.argv[2:7], *(int(a) for a in sys.argv[7:8]))
