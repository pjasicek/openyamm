#!/usr/bin/env python3
"""review/viewer/manifest.json for the three tier GLBs (viewer_export.py) and every clip (durations = GLB lengths)."""
import json, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
info = json.load(open(ROOT / 'work' / 'anim_info.json'))['clips']
notes = {'Standing': 'Hover bob 1.5 cm, slow tilt, cables trail back and sway, thrust pulse 3 Hz',
         'Walking': 'Forward flight: nose down 8 deg, cables stream back, thrust 5 Hz',
         'Running': 'Fast flight: nose down 15 deg, cables stream far back, thrust 8 Hz',
         'Attack': 'Aim, the shot at 0.292 s: recoil kick, lens punches in',
         'Hit': 'Knocked back, yaw and roll, damped wobble',
         'Death': 'Shudder, thrust cuts out, iris closes, drops, hits the floor at 0.875 s, comes to rest',
         'Dead': 'Held last pose of Death', 'Fidget': 'Scan turn left and right'}
loops = {'Standing', 'Walking', 'Running', 'Dead'}
models = []
for t, label in (('a', 'A: Seeker Drone (10050) - bone-white casing, violet resin, orange glow'),
                 ('b', 'B: Hunter Drone (10051) - scorched ivory, black resin, orange-red glow, twin emitter'),
                 ('c', 'C: Reaver Drone (10052) - blackened casing, gold trim, deep violet resin, orange-white glow, shield ring')):
    sha = hashlib.sha256((V / f'hes_drone_{t}.glb').read_bytes()).hexdigest()
    models.append({'id': f'hdr_{t}', 'label': label, 'revision': 'hes_drone_claude_v2', 'url': f'hes_drone_{t}.glb?v={sha[:12]}', 'sha256': sha})
src = ['../../../../../design/kreegan_world/concepts/monsters/fam_drones.png']
man = {'revision': 'hes_drone_claude_v2', 'model': 'hes_drone_a.glb', 'default_clip': 'Standing',
       'feedback': 'feedback/user_feedback.json', 'default_model': 'hdr_a', 'models': models,
       'clips': {k: {'label': k, 'duration': info[k]['seconds'], 'mode': 'loop' if k in loops else 'once', 'provenance': notes[k],
                     'anchors': [{'time': 0.0, 'label': k, 'phase': notes[k], 'source_images': src}]} for k in notes},
       'model_sha256': models[0]['sha256']}
json.dump(man, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', [m['url'] for m in models])
