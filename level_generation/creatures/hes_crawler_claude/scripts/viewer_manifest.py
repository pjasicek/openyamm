#!/usr/bin/env python3
"""Review viewer manifest: tiers (review/viewer/hes_crawler_<t>.glb, tier colours baked, B with its egg pods and C with
its acid sacs joined in, since three.js has neither region ramps nor actors.yml attachments), clip durations read from
the GLB, the approved concept / HD masters as reference images, cache-busting hashes."""
import json, hashlib, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'review' / 'viewer'
TIERS = [('crawler_a', 'A: Acid Crawler (10090) - pale bone-grey carapace, green acid'),
         ('crawler_b', 'B: Brood Crawler (10091) - rust-brown carapace, yellow-green acid, egg pods'),
         ('crawler_c', 'C: Crawler Matron (10092) - violet-black carapace, bright lime acid, swollen sacs')]
CLIPS = {'Standing': ('loop', 'breathing, throat-sac pulse, mandibles working'),
         'Walking': ('loop', 'alternating tetrapod scuttle, 2.4 model m/s (stride 0.48 m)'),
         'Running': ('loop', 'lower and faster tetrapod, 4.8 model m/s (stride 0.80 m)'),
         'Attack': ('once', 'rear up and spit acid: release from Socket_Mouth at 0.60 s'),
         'Bite': ('once', 'melee lunge, mandibles snap shut at 0.38 s'),
         'Hit': ('once', 'jolt back and down, legs splay, sac wobbles'),
         'Death': ('once', 'rears, rolls onto its back, legs fold over the belly, body curls'),
         'Dead': ('once', 'the corpse on its back'),
         'Fidget': ('loop', 'head sweeps left and right, front legs tap, mandibles clean')}
raw = (V / 'hes_crawler_a.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
dur = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
rev = 'hes_crawler_claude_v1'
m = {'revision': rev, 'model': 'hes_crawler_a.glb', 'default_clip': 'Standing', 'feedback': 'feedback/user_feedback.json',
     'default_model': 'crawler_a', 'models': [], 'clips': {}}
for vid, lab in TIERS:
    h = hashlib.sha256((V / f'hes_crawler_{vid[-1]}.glb').read_bytes()).hexdigest()
    m['models'].append({'id': vid, 'label': lab, 'revision': rev, 'url': f'hes_crawler_{vid[-1]}.glb?v={h[:12]}', 'sha256': h})
m['model_sha256'] = m['models'][0]['sha256']
imgs = ['../../references_hd/concept.png', '../../references_hd/03_left.png']
for k, (mode, prov) in CLIPS.items():
    m['clips'][k] = {'label': k, 'duration': dur[k], 'mode': mode, 'provenance': prov,
                     'anchors': [{'time': 0.0, 'label': k, 'phase': prov, 'source_images': imgs}]}
json.dump(m, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', {k: round(v, 3) for k, v in dur.items()})
