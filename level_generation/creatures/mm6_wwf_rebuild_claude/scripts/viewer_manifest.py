#!/usr/bin/env python3
"""review/viewer/manifest.json: before/after per tier (review/viewer/ttn_<tier>_<tag>.glb), every clip of the new GLB."""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'
doc, binary = read_glb(HERE / 'export/mm6_wwf.glb')
import struct
def dur(an):
    m = 0
    for s in an['samplers']:
        a = doc['accessors'][s['input']]; m = max(m, a['max'][0])
    return round(m, 6)
loops = {"Standing", "Walking", "Running", "Sprint"}
clips = {an['name']: {'label': an['name'], 'duration': dur(an), 'mode': 'loop' if an['name'] in loops else 'once',
                      'provenance': 'installed clip + finger keys' + (' + recovery fix' if an['name'] == 'Cast' else ''),
                      'anchors': []} for an in doc['animations']}
models = []
for tier in ('a', 'b', 'c'):
    for tag, label in (("new", "rebuild"), ("before", "installed")):
        f = V / f'wwf_{tier}_{tag}.glb'
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        extra = {'clip_map': {'Attack': 'Attack'}} if tag == 'before' else {}
        models.append({**extra, 'id': f'wwf_{tier}_{tag}', 'label': f'wwf_{tier} · {label}', 'url': f'{f.name}?v={h[:12]}',
                       'revision': 'rebuild-1', 'sha256': h})
json.dump({'revision': 'rebuild-1', 'model': 'MM6 Werewolf - rebuild on the MM9 BIGFOOT skeleton and clips',
           "default_clip": "Attack", 'feedback': 'feedback/user_feedback.json', "default_model": "wwf_a_new", 'models': models, 'clips': clips},
          open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models), 'models', len(clips), 'clips')
