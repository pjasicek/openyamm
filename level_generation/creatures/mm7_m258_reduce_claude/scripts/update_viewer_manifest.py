#!/usr/bin/env python3
"""Reduction review viewer manifest (copied from mm7_m258_claude): the pre-reduction model and the reduced one
(smooth shading, plus the flat-shaded alternative for tier A) per tier, clip durations read from the GLB, native
reference frames per clip, cache-busting hashes on the model URLs."""
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
raw = (V / 'mm7_m258_r57_m258_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'reduce-1', 'model': 'mm7_m258_r57_m258_a.glb', 'default_clip': 'Fly',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'a_r57', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
TIERS = (('m258_a', 'Griffin A'), ('m258_b', 'Hunting Griffin B'), ('m258_c', 'Royal Griffin C'))
ITEMS = [(f'{t[-1]}_r100', 'r100', t, f'{lab} \u00b7 pre-reduction \u00b7 16,126') for t, lab in TIERS]
ITEMS += [(f'{t[-1]}_r57', 'r57', t, f'{lab} \u00b7 reduced 57 % smooth \u00b7 9,188') for t, lab in TIERS]
ITEMS += [('a_r57flat', 'r57flat', 'm258_a', 'Griffin A \u00b7 reduced 57 % flat-shaded \u00b7 9,188')]
for vid, label, tier, lab in ITEMS:
    f = f'mm7_m258_{label}_{tier}.glb'; h = _h.sha256((V / f).read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'reduce-1', 'url': f'{f}?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m258sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
