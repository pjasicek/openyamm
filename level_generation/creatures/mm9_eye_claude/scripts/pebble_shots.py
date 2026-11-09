#!/usr/bin/env python3
"""Identical review-viewer close-ups of the hide for the pebble pass, every tier and stage. Fixed cameras, because the
viewer's presets frame a standing humanoid (same viewer_shots.mjs as tools/run_creature_review.py).
Stages: approved (pre texture pass), texpass (the smooth hide), restored (review/viewer).
Usage: pebble_shots.py <stage> [port] -> review/pebble_viewer/<stage>/<tier>_<shot>.png"""
import json, subprocess, sys
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
stage, port = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '8912'
# review/viewer_approved and viewer_texpass are symlinks to work/before_texpass/viewer and work/before_pebbles/viewer: the
# viewer page imports three.js by a path relative to review/<viewer>/
VIEWERS = {'approved': HERE / 'review/viewer_approved', 'texpass': HERE / 'review/viewer_texpass',
           'restored': HERE / 'review/viewer'}
# name: clip, time, camera, target (glTF metres)
SHOTS = {'back': ('Standing', 0, (0.3, 3.15, -1.45), (0, 3.05, 0)),
         'side': ('Standing', 0, (1.5, 3.1, 0.05), (0, 3.0, 0)),
         'top': ('Standing', 0, (-0.3, 4.2, -0.7), (0, 3.2, 0)),
         'jaw': ('Standing', 0, (-0.9, 2.5, 1.25), (0, 2.75, 0.2)),
         'stalk': ('Standing', 0, (1.2, 3.9, -1.5), (0.7, 3.7, -0.6)),
         'full': ('Standing', 0, (-3.6, 2.6, -4.8), (0, 2.2, 0))}
view = VIEWERS[stage]
man = json.loads((view / 'manifest.json').read_text())
out = HERE / 'review/pebble_viewer' / stage
out.mkdir(parents=True, exist_ok=True)
tmp = HERE / 'review/shots'
for model in man['models']:
    url = f'http://127.0.0.1:{port}/{view.relative_to(REPO).as_posix()}/#' + \
        quote(json.dumps({'clip': man['default_clip'], 'model_sha256': model['sha256']}))
    specs = [f'pb_{n}:{c}:{t}:front:body:{",".join(map(str, cam))}:{",".join(map(str, tgt))}'
             for n, (c, t, cam, tgt) in SHOTS.items()]
    subprocess.run(['node', str(HERE.parent / 'mm8_m424_claude/scripts/viewer_shots.mjs'), url, str(tmp), *specs],
                   check=True, cwd=REPO)
    for n in SHOTS:
        (tmp / f'pb_{n}.png').rename(out / f'{model["id"]}_{n}.png')
print('SHOTS', stage, len(man['models']) * len(SHOTS))
