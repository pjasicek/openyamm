#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m298' / 'trimmed_2x'
REL = '../../../mm7_m298/trimmed_2x'
clips = {
 'Standing': ('loop', 'Slow pulse: the lumps breathe out of phase (native: one still frame)', ['m298sa0', 'm298sa1', 'm298sa2']),
 'Walking': ('loop', 'Native wa..wf: the middle heaves into a hump and settles, a peristaltic wave runs front to back; 0.75 s, stride 0.5 m', [f'm298w{c}0' for c in 'abcdef']),
 'Running': ('loop', 'The crawl larger and faster: 0.5 s, stride 0.5 m', [f'm298w{c}0' for c in 'abcdef']),
 'Attack': ('once', 'Native a b c d e f e d c b: a knobbed pseudopod rises, curls back, stands tallest, lashes forward and down (impact 0.68 s), retracts; 1.25 s', [f'm298a{c}2' for c in 'abcdef']),
 'Cast': ('once', 'Toxic Cloud (B/C): the pod rises straight, the knob swells and spits at 0.68 s (Socket_Spit), sinks back; 1.25 s', [f'm298a{c}0' for c in 'abcdef']),
 'Hit': ('once', 'Native na..ng: the outline draws in and the middle heaves into a cone, then relaxes; 0.875 s', [f'm298n{c}0' for c in 'abcdefg']),
 'Death': ('once', 'Native da..de: contracts, gathers into a column and hops, bursts into globules that rain down around a small remnant; 0.625 s', ['m298da0', 'm298db0', 'm298dc0', 'm298dd0', 'm298de0']),
 'Dead': ('loop', 'Corpse (native xa): scattered globules held', ['m298xa0']),
 'Fidget': ('once', 'Native fa..fe: two bubbles swell out of the top and pop; 0.625 s', [f'm298f{c}0' for c in 'abcde']),
}
raw = (V / 'mm7_m298_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m298_claude_v1', 'model': 'mm7_m298_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm298_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m298_a', 'Emerald Ooze - A'), ('m298_b', 'Sapphire Ooze - B'), ('m298_c', 'Bloodstone Ooze - C')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m298_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m298sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
