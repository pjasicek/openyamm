#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m242' / 'aligned_2x'
REL = '../../../mm7_m242/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Zombie Idle upper body, 70 % of the reaching arms; hover with a slow bob; robe chains sway', ['m242sa0', 'm242sa1', 'm242sa2']),
 'Walking': ('loop', 'Authored swoop: body pitched forward, arms reaching (Zombie Walk), the robe trailing back on chains with a travelling wave (1.0 s)', [f'm242w{c}2' for c in 'abcdefgh']),
 'Attack': ('once', 'Mixamo Zombie Attack window: both claws raised over the hood, then a forward lunge with the claws; blow 1.017 s', [f'm242a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Mixamo Zombie Reaction Hit (first 0.8 s), the robe jolts back', [f'm242n{c}0' for c in 'abcdef']),
 'Death': ('once', 'Authored: arms rise, the empty robe collapses straight down into a heap, the arms fall onto the floor', ['m242da0', 'm242db0', 'm242dc0', 'm242dd0']),
 'Dead': ('loop', 'Last Death pose held', ['m242xa0']),
 'Fidget': ('once', 'Mixamo Zombie Scream: arms flung wide, the robe flares', ['m242fa0', 'm242fb0', 'm242fc0', 'm242fd0']),
}
raw = (V / 'mm7_m242_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m242_claude_v1', 'model': 'mm7_m242_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm242_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m242_a', 'Shade - A (palette 243, grey-white robe)'), ('m242_b', 'Specter - B (244, brown robe: native art)'), ('m242_c', 'Ghost - C (245, near-black robe)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m242_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m242sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
