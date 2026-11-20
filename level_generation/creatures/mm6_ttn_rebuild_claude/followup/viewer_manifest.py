#!/usr/bin/env python3
"""Follow-up viewer manifest: review/viewer/ttn_<tier>_<tag>.glb for the tags given (first = default), plus 'cur'
(installed before the follow-up) and 'before' (pre-rebuild). Usage: viewer_manifest.py <glb for clips> <tag> [tag ...]"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'
doc, _ = read_glb(Path(sys.argv[1])); tags = sys.argv[2:]
dur = lambda an: round(max(doc['accessors'][s['input']]['max'][0] for s in an['samplers']), 6)
loops = {'Standing', 'Walking', 'WalkHeavy', 'Running'}
clips = {an['name']: {'label': an['name'], 'duration': dur(an), 'mode': 'loop' if an['name'] in loops else 'once',
                      'provenance': 'installed clip + finger keys', 'anchors': []} for an in doc['animations']}
labels = {'cur': 'five-finger hands (before follow-up)', 'before': 'pre-rebuild'}
models = []
for tier in ('a', 'b', 'c'):
    for tag in tags + [t for t in ('cur', 'before') if t not in tags]:
        f = V / f'ttn_{tier}_{tag}.glb'
        if f.exists():
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            models.append({'id': f'ttn_{tier}_{tag}', 'label': f'ttn_{tier} · {labels.get(tag, "follow-up " + tag)}',
                           'url': f'{f.name}?v={h[:12]}', 'revision': 'followup', 'sha256': h})
json.dump({'revision': 'followup-1', 'model': 'MM6 Titan - five-finger hands, follow-up (clean fists)', 'default_clip': 'Fidget',
           'feedback': 'feedback/user_feedback.json', 'default_model': f'ttn_a_{tags[0]}', 'models': models, 'clips': clips},
          open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models), 'models', len(clips), 'clips')
