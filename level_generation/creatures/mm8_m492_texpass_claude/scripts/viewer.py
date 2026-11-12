#!/usr/bin/env python3
"""Review viewer of the texture pass: index.html/review.js from the Troll texpass viewer (title, storage key and camera
focuses from texpass.json), per-variant GLBs with the region ramps baked (viewer_variants.py) for every target GLB as
<variant>_before (work/before_texpass/<stem>.glb) and <variant>_tp (export/<stem>.glb), and manifest.json with the
production viewer's clips (texpass.json production_viewer; relative source-image paths rebased).
Usage: viewer.py [default model id]"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import tp

V = tp.HERE / 'review' / 'viewer'
V.mkdir(parents=True, exist_ok=True)
SRC = tp.CREATURES / 'mm8_m480_texpass_claude' / 'review' / 'viewer'
title = tp.CFG.get('title', tp.HERE.name)
html = (SRC / 'index.html').read_text()
html = re.sub(r'<title>.*?</title>', f'<title>{title} texture pass</title>', html)
html = re.sub(r'<h1>.*?</h1><p>.*?</p>', f'<h1>{title} texture pass ({tp.HERE.name})</h1><p>Installed (before) and '
              'texture-pass (tp) versions per tier; region ramps baked for three.js. Mesh, rig and clips are the '
              'installed ones.</p>', html)
(V / 'index.html').write_text(html)
js = (SRC / 'review.js').read_text()
js = js.replace("'openyamm:mm6-natm-claude:notes'", f"'openyamm:{tp.HERE.name}:notes'")
js = js.replace('Troll texpass', f'{title} texpass')
focuses = tp.CFG.get('focuses')
if focuses:
    js = re.sub(r'const focuses = \{.*?\};', 'const focuses = ' + json.dumps(focuses).replace('"', '') + ';', js)
(V / 'review.js').write_text(js)

tags = []
for world, stem in tp.CFG['targets']:
    for tag, path in (('before', tp.HERE / 'work' / 'before_texpass' / f'{stem}.glb'),
                      ('tp', tp.HERE / 'export' / f'{stem}.glb')):
        if path.exists():
            subprocess.run([sys.executable, str(Path(__file__).parent / 'viewer_variants.py'), str(path), tag], check=True)
            tags.append(tag)
prod_path = tp.CREATURES / tp.CFG['production_viewer']
prod = json.loads(prod_path.read_text())
rel = '../../../' + prod_path.parent.parent.parent.name + '/'
clips = json.loads(json.dumps(prod['clips']).replace('"../../', '"' + rel))
for clip in clips.values():         # drop native reference frames that are not on disk (404s in the viewer check)
    for anchor in clip.get('anchors', []):
        if 'source_images' in anchor:
            anchor['source_images'] = [x for x in anchor['source_images'] if (V / x).resolve().exists()]
    if 'anchors' in clip:
        clip['anchors'] = [a for a in clip['anchors'] if a.get('source_images', [None])]
models = []
for tier, label in tp.CFG['tiers'].items():
    for tag in ('before', 'tp'):
        f = V / f'{tier}_{tag}.glb'
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'{tier}_{tag}', 'label': f'{label} · {"installed" if tag == "before" else "texture pass"}',
                       'url': f'{f.name}?v={h[:12]}', 'sha256': h, 'revision': 'texpass-20261111'})
default = sys.argv[1] if len(sys.argv) > 1 else models[-1]['id']
pick = next(m for m in models if m['id'] == default)
manifest = {'revision': 'texpass-20261111', 'default_model': default,
            'default_clip': prod.get('default_clip', next(iter(clips))), 'models': models, 'clips': clips,
            'issues': [], 'feedback': 'feedback/user_feedback.json', 'model': pick['url'], 'model_sha256': pick['sha256']}
if 'fps' in prod:
    manifest['fps'] = prod['fps']
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
(V / 'feedback').mkdir(exist_ok=True)
if not (V / 'feedback' / 'user_feedback.json').exists():
    (V / 'feedback' / 'user_feedback.json').write_text(json.dumps({'findings': []}) + '\n')
print('MANIFEST', len(models), 'models')
