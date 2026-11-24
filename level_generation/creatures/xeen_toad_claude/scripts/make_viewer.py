#!/usr/bin/env python3
"""Review viewer for the toad (D-118): copies the shared Xeen viewer page (xeen_armadillo_claude's index.html and
review.js, names replaced) and writes review/viewer/manifest.json for export/xeen_toad_lod0.glb (the Blender export:
Toad_A, the native skin, plus Mouth and Tongue; three.js draws no region ramps). Clip lengths from work/anim_info.json."""
import hashlib, json, shutil
from pathlib import Path
here = Path(__file__).resolve().parents[1]
src = here.parent / 'xeen_armadillo_claude' / 'review' / 'viewer'
out = here / 'review' / 'viewer'
(out / 'feedback').mkdir(parents=True, exist_ok=True)
for name in ('index.html', 'review.js'):
    text = (src / name).read_text()
    text = text.replace('xeen-armadillo-claude', 'xeen-toad-claude').replace('xeen:armadillo', 'xeen:toad')
    text = text.replace('xeen_armadillo_claude', 'xeen_toad_claude').replace('Xeen armadillo', 'Xeen toad')
    if name == 'index.html':
        start = text.index('<header>'); end = text.index('</header>') + len('</header>')
        text = text[:start] + ('<header><h1>Xeen Giant Toad (xeen_toad_claude)</h1><p>Giant Toad (Clouds of Xeen '
                               'image 13), D-118 repair: mouth cavity on its own material and a Jaw bone, hind-leg '
                               'weights and limited hops, tongue kept in when dying. Native skin (toad_a).</p>'
                               '</header>') + text[end:]
    (out / name).write_text(text)
fb = out / 'feedback' / 'user_feedback.json'
if not fb.exists():
    fb.write_text('{"findings": []}\n')
glb = out / 'xeen_toad_a.glb'
shutil.copyfile(here / 'export' / 'xeen_toad_lod0.glb', glb)
sha = hashlib.sha256(glb.read_bytes()).hexdigest()
info = json.loads((here / 'work' / 'anim_info.json').read_text())['clips']
what = {'Standing': 'breathing, throat pulses twice', 'Walking': 'short hops, 1.30 m per cycle',
        'Running': 'long hops, 2.40 m per cycle', 'Attack': 'low rear, the jaw opens, tongue strike at 0.42 s',
        'Hit': 'jolt back and down', 'Death': 'convulsive leap, flips onto its back, tongue kept in',
        'Dead': 'on its back', 'Fidget': 'throat puffs, head turns, a short tongue flick'}
images = {'Attack': ['../../native/att_0000.png', '../../native/att_0002.png'], 'Walking': ['../../native/sheet_leap.png']}
clips = {}
for name, d in info.items():
    clips[name] = {'label': name, 'duration': d['frames'] / 30, 'mode': 'once' if name in ('Attack', 'Hit', 'Death', 'Fidget') else 'loop', 'provenance': what[name],
                   'anchors': [{'time': 0.0, 'label': name, 'phase': what[name],
                                'source_images': images.get(name, ['../../native/mon_0000.png'])}]}
manifest = {'revision': 'xeen_toad_claude_d118', 'model': glb.name, 'default_clip': 'Attack',
            'feedback': 'feedback/user_feedback.json', 'default_model': 'toad_a', 'model_sha256': sha,
            'models': [{'id': 'toad_a', 'label': 'Giant Toad (Xeen Toad A, native skin)',
                        'revision': 'xeen_toad_claude_d118', 'url': f'{glb.name}?v={sha[:12]}', 'sha256': sha}],
            'clips': clips}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
print('VIEWER', out, sha[:12])
