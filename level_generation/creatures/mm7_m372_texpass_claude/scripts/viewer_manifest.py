#!/usr/bin/env python3
"""review/viewer/manifest.json for the m372 texture pass: every review/viewer/<variant>_<tag>.glb of the given tags,
in tag order per skin. Clips and durations are read from the GLB itself (the installed file carries Walk2 and Jog
beyond the production viewer's six); native anchors are taken from the production manifest where the names match.
Usage: viewer_manifest.py <default model id> <tag>[=label] ..."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
V = HERE / 'review/viewer'
REV = 'texpass-20261101-r3'
TIERS = {'m372_aa': 'AA FemaleA A (green / sage / auburn)', 'm372_ab': 'AB FemaleA B (blue / blue-grey / blonde)',
         'm372_ac': 'AC FemaleA C (red / rose / dark auburn)', 'm372_ba': 'BA FemaleB+C A (green / sage / blonde)',
         'm372_bb': 'BB FemaleB+C B (blue / blue-grey / auburn)', 'm372_bc': 'BC FemaleB+C C (red / rose / blonde)'}
default = sys.argv[1]
tags = [a.split('=', 1) if '=' in a else (a, a) for a in sys.argv[2:]]
prod = json.loads((HERE.parent / 'mm7_m372_claude/review/viewer/manifest.json').read_text())
models = []
for tier, name in TIERS.items():
    for tag, label in tags:
        f = V / f'{tier}_{tag}.glb'
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'{tier}_{tag}', 'label': f'{name} · {label}', 'url': f'{f.name}?v={h[:12]}',
                       'sha256': h, 'revision': REV})
g = Glb(HERE / 'work/before_texpass/mm7_m372.glb')
clips = {}
for a in g.doc['animations']:
    dur = max(float(g.accessor(s['input']).max()) for s in a['samplers'])
    base = prod['clips'].get(a['name'], {})
    mode = 'once' if a['name'] in ('Death', 'Hit') else 'loop'
    clip = {'label': a['name'], 'duration': round(dur, 6), 'mode': base.get('mode', mode),
            'provenance': base.get('provenance', 'installed clip'), 'anchors': base.get('anchors', [])}
    clips[a['name']] = clip          # anchor paths are relative to a project viewer: the same depth here
pick = next(m for m in models if m['id'] == default)
manifest = {'revision': REV, 'default_model': default, 'default_clip': 'Standing', 'models': models,
            'clips': clips, 'issues': [], 'feedback': 'feedback/user_feedback.json', 'model': pick['url'],
            'model_sha256': pick['sha256']}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
print('MANIFEST', len(models), 'models', {k: v['duration'] for k, v in clips.items()})
