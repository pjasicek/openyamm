#!/usr/bin/env python3
"""Writes review/viewer/manifest.json for the tier GLBs from viewer_tiers.py, with clip lengths from the installed
LOD0 and native frame anchors (palettes 429/430/431)."""
import hashlib, json, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / 'review' / 'viewer'
raw = (ROOT / 'export' / 'mm8_m428_runtime_lod0.glb').read_bytes()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n])
durations = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
PROVENANCE = {'Standing': 'Standard idle holding the dagger', 'Walking': "The male peasant's walk",
              'Running': 'Standard run fitted to her body (flee)', 'Hit': 'Standard recoil',
              'Death': 'Backward fall, legs together under the dress', 'Dead': 'Final death pose held',
              'Fidget': 'Authored from native frames: raises the dagger, fingers along the blade'}
FRAMES = {'Standing': ['sa'], 'Walking': ['w' + c for c in 'abcdefgh'], 'Running': ['w' + c for c in 'abcdefgh'],
          'Hit': ['n' + c for c in 'abcd'], 'Death': ['na', 'nb', 'da', 'db', 'dc'], 'Dead': ['xa'],
          'Fidget': ['f' + c for c in 'abcd']}
manifest = {'revision': 'mm8_m428_claude_v1', 'model': 'mm8_m428_a.glb', 'default_model': 'm428_a',
            'default_clip': 'Standing', 'feedback': 'feedback/user_feedback.json', 'models': [], 'clips': {}}
for tier, label in [('a', 'Tier A — green'), ('b', 'Tier B — blue'), ('c', 'Tier C — red')]:
    path = VIEWER / f'mm8_m428_{tier}.glb'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest['models'].append({'id': 'm428_' + tier, 'label': label, 'revision': manifest['revision'],
                               'url': f'{path.name}?v={digest[:12]}', 'sha256': digest})
manifest['model_sha256'] = manifest['models'][0]['sha256']
for name, seconds in durations.items():
    stems = FRAMES[name]
    manifest['clips'][name] = {
        'label': name, 'duration': seconds,
        'mode': 'loop' if name in ('Standing', 'Walking', 'Running', 'Dead') else 'once',
        'provenance': PROVENANCE[name],
        'anchors': [{'time': i * seconds / max(1, len(stems) - 1), 'label': stem, 'phase': PROVENANCE[name],
                     'source_images': [f'../../../mm8_m428/native_variants/m428{stem}{view}_429.png'
                                       for view in range(5)]} for i, stem in enumerate(stems)]}
(VIEWER / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print('VIEWER clips', durations)
