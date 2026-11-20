#!/usr/bin/env python3
"""Follow-up viewer manifest: review/viewer/wwf_<tier>_<tag>.glb for the tags given (first = the default), e.g.
'fu cur' (follow-up, installed before it).
Clips from the GLB given. Usage: viewer_manifest.py <glb for clips> <tag> [tag ...]"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'
doc, _ = read_glb(Path(sys.argv[1])); tags = sys.argv[2:]
def dur(an):
    return round(max(doc['accessors'][s['input']]['max'][0] for s in an['samplers']), 6)
loops = {'Standing', 'Walking', 'Running', 'Sprint'}
clips = {an['name']: {'label': an['name'], 'duration': dur(an), 'mode': 'loop' if an['name'] in loops else 'once',
                      'provenance': 'rebuild clip', 'anchors': []} for an in doc['animations']}
labels = {'before': 'pre-rebuild', 'new': 'rebuild (before follow-up)'}
models = []
for tier in ('a', 'b', 'c'):
    for tag in tags:   # the pre-rebuild GLBs (wwf_*_before) have other clip durations: compare them by stored shots
        f = V / f'wwf_{tier}_{tag}.glb'
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({'id': f'wwf_{tier}_{tag}', 'label': f'wwf_{tier} · {labels.get(tag, "follow-up " + tag)}',
                       'url': f'{f.name}?v={h[:12]}', 'revision': 'followup', 'sha256': h})
json.dump({'revision': 'followup-1', 'model': 'MM6 Werewolf - rebuild on MM9 BIGFOOT, follow-up (fur tone, claws)',
           'default_clip': 'Attack', 'feedback': 'feedback/user_feedback.json', 'default_model': f'wwf_a_{tags[0]}',
           'models': models, 'clips': clips}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models), 'models', len(clips), 'clips')
