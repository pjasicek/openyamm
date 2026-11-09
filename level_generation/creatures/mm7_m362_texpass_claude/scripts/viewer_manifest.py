#!/usr/bin/env python3
"""review/viewer/manifest.json for the m362 texture pass: every review/viewer/m362_<skin>_<tag>.glb of the given tags,
in tag order per skin. Clips and durations come from the installed GLB itself (Standing, Walking, Jog loop; the rest
play once), with the production viewer's native anchors where it has them.
Usage: viewer_manifest.py <default model id> <revision> <tag>[=label] ..."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
V = HERE / 'review/viewer'
SKINS = {'m362_aa': 'MaleA A (violet, blond, shaven)', 'm362_ab': 'MaleA B (green, brown, grey beard)',
         'm362_ac': 'MaleA C (red, black, black beard)', 'm362_ba': 'MaleB A (violet, white, white beard)',
         'm362_bb': 'MaleB B (black, blond, blond beard)', 'm362_bc': 'MaleB C (olive, ginger, shaven)',
         'm362_ca': 'MaleC A (grey, dark brown, shaven)', 'm362_cb': 'MaleC B (brown, ginger, ginger beard)',
         'm362_cc': 'MaleC C (blue, grey, shaven)'}
LOOP = {'Standing', 'Walking', 'Jog', 'Dead'}
default, revision = sys.argv[1], sys.argv[2]
tags = [a.split('=', 1) if '=' in a else (a, a) for a in sys.argv[3:]]
g = Glb(HERE / 'work' / 'before_texpass' / 'mm7_m362.glb')
prod = json.loads((HERE.parent / 'mm7_m362_claude/review/viewer/manifest.json').read_text())['clips']
clips = {}
for anim in g.doc['animations']:
    duration = max(float(g.accessor(s['input']).max()) for s in anim['samplers'])
    old = prod.get(anim['name'], {})
    anchors = json.loads(json.dumps(old.get('anchors', [])).replace('"../../../mm7_m362/', '"../../../mm7_m362/'))
    clips[anim['name']] = {'label': anim['name'], 'duration': round(duration, 6),
                           'mode': 'loop' if anim['name'] in LOOP else 'once',
                           'provenance': 'installed clip (unchanged by the texture pass)', 'anchors': anchors}
models = []
for skin, name in SKINS.items():
    for tag, label in tags:
        f = V / f'{skin}_{tag}.glb'
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'{skin}_{tag}', 'label': f'{name} · {label}', 'url': f'{f.name}?v={h[:12]}',
                       'sha256': h, 'revision': revision})
pick = next(m for m in models if m['id'] == default)
manifest = {'revision': revision, 'default_model': default, 'default_clip': 'Standing', 'models': models,
            'clips': clips, 'issues': [], 'feedback': 'feedback/user_feedback.json', 'model': pick['url'],
            'model_sha256': pick['sha256']}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
print('MANIFEST', len(models), 'models', {k: v['duration'] for k, v in clips.items()})
