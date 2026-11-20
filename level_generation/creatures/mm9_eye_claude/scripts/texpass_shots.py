#!/usr/bin/env python3
"""Texture pass: identical review-viewer shots of every Eye tier. The viewer's focus presets frame a standing humanoid
and the hovering Eye floats above them, so this calls the wrapper's viewer_shots.mjs directly with fixed cameras
(the 6th/7th shot fields; run_creature_review.py accepts presets only).
Usage: texpass_shots.py <before|after> [port]  -> review/texpass_viewer/<stage>/<tier>_<shot>.png"""
import json, subprocess, sys
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
stage, port = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '8931'
# name: clip, time, camera, target (glTF metres)
SHOTS = {'full_q': ('Standing', 0, (-3.6, 2.6, 4.8), (0, 2.2, 0)),
         'full_r': ('Standing', 0, (-3.6, 2.6, -4.8), (0, 2.2, 0)),
         'face_f': ('Standing', 0, (0, 3.0, 2.4), (0, 3.0, 0)),
         'face_q': ('Standing', 0, (-1.5, 3.1, 1.9), (0, 3.0, 0)),
         'macro': ('Standing', 0, (0, 3.0, 1.3), (0, 3.0, 0)),
         'side': ('Standing', 0, (2.3, 3.0, 0.2), (0, 3.0, 0)),
         'back': ('Standing', 0, (0.4, 3.1, -2.2), (0, 3.0, 0)),
         'under': ('Standing', 0, (0.3, 1.4, 1.6), (0, 2.7, 0)),
         'legs': ('Standing', 0, (-0.8, 1.2, 1.9), (0, 1.1, 0)),
         'jaw': ('AttackMelee', 0.48, (-1.2, 2.3, 3.6), (0.5, 2.0, 0))}
man = json.loads((HERE / 'review/viewer/manifest.json').read_text())
out = HERE / 'review/texpass_viewer' / stage
out.mkdir(parents=True, exist_ok=True)
tmp = HERE / 'review/shots'
for model in man['models']:
    url = f'http://127.0.0.1:{port}/{(HERE / "review/viewer").relative_to(REPO).as_posix()}/#' + \
        quote(json.dumps({'clip': man['default_clip'], 'model_sha256': model['sha256']}))
    specs = [f'tp_{n}:{c}:{t}:front:body:{",".join(map(str, cam))}:{",".join(map(str, tgt))}'
             for n, (c, t, cam, tgt) in SHOTS.items()]
    subprocess.run(['node', str(HERE.parent / 'mm8_m424_claude/scripts/viewer_shots.mjs'), url, str(tmp), *specs],
                   check=True, cwd=REPO)
    for n in SHOTS:
        (tmp / f'tp_{n}.png').rename(out / f'{model["id"]}_{n}.png')
