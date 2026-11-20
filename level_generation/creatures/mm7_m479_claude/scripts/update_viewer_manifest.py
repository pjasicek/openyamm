#!/usr/bin/env python3
"""Review viewer manifest from the viewer GLB: clip durations read from the GLB, native reference frames per clip,
cache-busting hash on the model URL. One model (no tiers: palette 530 for all three descriptors)."""
import json, hashlib, struct
from pathlib import Path
V = Path(__file__).resolve().parents[1] / 'review' / 'viewer'
NAT = Path(__file__).resolve().parents[2] / 'mm7_m479' / 'trimmed_2x'
REL = '../../../mm7_m479/trimmed_2x'
clips = {
 'Standing': ('loop', 'Disguise (native m479sa0, also walk/fidget): mouth closed, eyes sunk, slow wind sway', ['m479sa0']),
 'Attack': ('once', 'Wakes, winds up back-right, whip-lash forward-left with every limb sweeping forward (impact 0.6875 s); also the ranged Earth attack', [f'm479a{c}0' for c in 'bcdefghijklmnopqrs']),
 'Hit': ('once', 'Eyes open, mouth gapes, recoil and limb shudder (native 0.4375 s)', [f'm479n{c}0' for c in 'abcdefg']),
 'Death': ('once', 'Limbs snap off and splinter, spire and upper trunk collapse onto a toothed stump', ['m479da0', 'm479db0', 'm479dc0', 'm479dd0']),
 'Dead': ('loop', 'Last Death pose held (native corpse m479xa0)', ['m479xa0']),
}
raw = (V / 'mm7_m479.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
sha = hashlib.sha256(raw).hexdigest()
m = {'revision': 'mm7_m479_claude_v1', 'model': 'mm7_m479.glb', 'default_clip': 'Standing',
     'feedback': 'feedback/user_feedback.json', 'default_model': 'm479', 'model_sha256': sha,
     'models': [{'id': 'm479', 'label': 'Treant A / B / C (palette 530, all tiers identical)',
                 'revision': 'mm7_m479_claude_v1', 'url': f'mm7_m479.glb?v={sha[:12]}', 'sha256': sha}],
     'clips': {}}
for k, (mode, prov, imgs) in clips.items():
    imgs = [i for i in imgs if (NAT / f'{i}.png').exists()] or ['m479sa0']
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': [f'{REL}/{i}.png' for i in imgs]}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
