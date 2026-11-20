#!/usr/bin/env python3
"""Review viewer manifest from the exported clay GLB: clip durations read from the GLB, native reference frames per
clip, cache-busting hash on the model URL."""
import json, hashlib, struct, os
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m254' / 'aligned_2x'
REL = '../../../mm7_m254/aligned_2x'
clips = {
 'Standing': ('loop', 'Mixamo Orc Idle: arms held out, bent elbows, clawed hands, slight forward lean (native m254sa)', ['m254sa0', 'm254sa1', 'm254sa2']),
 'Walking': ('loop', 'Mixamo Walk, pelvis bob low-passed (heavy, even gait); plays at 0.64-0.72x in game', [f'm254w{c}0' for c in 'abcdefgh']),
 'Running': ('loop', 'Mixamo Standard Run fitted (never reached at the tier speeds)', [f'm254w{c}0' for c in 'abcdefgh']),
 'Attack': ('once', 'Double-fist smash: authored arms (both straight up, then both fists down in front) over the set 2H axe chop 5 trunk and legs, planted, faced front; blow 0.967 s', [f'm254a{c}0' for c in 'abcdefgh']),
 'Hit': ('once', 'Humanoid set Unarmed get-hit front 1; blends 0.2 s', [f'm254n{c}0' for c in 'abcde']),
 'Death': ('once', 'Mixamo Standing React Death Backward (travel halved): falls onto the back (native m254na/nb, da..dd)', ['m254na0', 'm254nb0', 'm254da0', 'm254db0', 'm254dc0', 'm254dd0']),
 'Dead': ('loop', 'Last Death pose held (native corpse m254xa)', ['m254xa0']),
 'Fidget': ('once', 'Mixamo Mutant Flexing Muscles (planted, 20 % legs): the native flex (m254fa..fe)', [f'm254f{c}0' for c in 'abcde']),
}
raw = (V / 'mm7_m254_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m254_claude_v1', 'model': 'mm7_m254_a.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm254_a', 'model_sha256': sha,
     'models': [],
     'clips': {}}
import hashlib as _h
for vid, lab in (('m254_a', 'Bronze Golem - A (palette 255, green stripes)'), ('m254_b', 'Brass Golem - B (256, cyan / blue stripes)'), ('m254_c', 'Gold Golem - C (257, tan / red stripes)')):
    h = _h.sha256((V / f'mm7_{vid}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': 'mm7_m254_claude_v1', 'url': f'mm7_{vid}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m254sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
