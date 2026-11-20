#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m258' / 'trimmed_2x'
REL = '../../../mm7_m258/trimmed_2x'
clips = {
 'Fly': ('loop', 'Procedural wing beat on the native 0.875 s rhythm (standing, walking, running and fidget)', [f'm258w{c}0' for c in 'abcdefg']),
 'Attack': ('once', 'Rears up with the wings raised, rakes both talons forward and down with a hard downbeat (impact 0.55 s)', [f'm258a{c}0' for c in 'abcdefg']),
 'Hit': ('once', 'Jolts back and up, wings flare, legs flail, recovers', [f'm258n{c}0' for c in 'abcdefg']),
 'Death': ('once', 'Wings fold, tumbles over onto its back, wings spread flat on landing', ['m258na0', 'm258nb0', 'm258da0', 'm258db0', 'm258dc0', 'm258dd0']),
 'Dead': ('loop', 'Last Death pose held', ['m258xa0']),
}
raw = (V / 'mm7_m258_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m258_claude_v1', 'model': 'mm7_m258_a.glb', 'default_clip': 'Fly',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm258_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m258_a', 'Griffin - A (teal)'), ('m258_b', 'Hunting Griffin - B (blue-grey)'), ('m258_c', 'Royal Griffin - C (crimson)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m258_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m258sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
