#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m162' / 'trimmed_2x'
REL = '../../../mm7_m162/trimmed_2x'
clips = {
 'Standing': ('loop', 'Mixamo Mutant Breathing Idle, relative to its first frame (= the modelled native hunch)', ['m162sa0', 'm162sa1', 'm162sa2']),
 'Walking': ('loop', 'Mixamo Mutant Walking, in place, arms abducted 9 deg (thighs)', [f'm162w{c}2' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Mutant Run, lifted out of the floor only', [f'm162w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Mutant Swiping (chest held on the party): right arm raised overhead (native m162nb), wind-up 1.6x, 0.25 s slam of the left claws into the floor in front (impact 0.856 s), source recovery', [f'm162a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Mixamo zombie reaction hit relative to its first frame, 1.1 s, eased out', [f'm162n{c}0' for c in 'abcd']),
 'Death': ('once', 'Mixamo Zombie Dying relative to its first frame: staggers, kneels, falls flat on its face (native corpse m162xa0); travel halved', ['m162da0', 'm162db0', 'm162dc0', 'm162dd0']),
 'Dead': ('loop', 'Last Death pose held', ['m162xa0']),
 'Fidget': ('once', 'Mixamo Mutant Roaring', [f'm162f{c}0' for c in 'abcde']),
}
raw = (V / 'mm7_m162_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m162_claude_v1', 'model': 'mm7_m162_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm162_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m162_a', 'Young Behemoth - A (green)'), ('m162_b', 'Behemoth - B (blue-violet)'), ('m162_c', 'Ancient Behemoth - C (red)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m162_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m162sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
