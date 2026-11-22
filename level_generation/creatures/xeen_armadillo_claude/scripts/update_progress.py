#!/usr/bin/env python3
"""Write the non-Meshy fields of creature_3d_progress.json (run under the lease: creature_workspace.py run)."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
p = ROOT / 'creature_3d_progress.json'
d = json.loads(p.read_text())
sha = lambda f: hashlib.sha256(Path(f).read_bytes()).hexdigest()
d['required_components'] = [{'id': 'body', 'artifact_role': 'body', 'required': True,
                             'note': 'one mesh: body, head, face caps, four clawed feet, tail with mace ball, '
                                     'procedural ball spikes (Spikes bone) and forked tongue (Tongue bone)'}]
d['installed'] = {'source': 'assets_source/worlds/xeen/models/xeen_armadillo.glb',
                  'sha256': sha(REPO / 'assets_source/worlds/xeen/models/xeen_armadillo.glb'),
                  'runtime_sha256': sha(REPO / 'assets_dev/worlds/xeen/models/xeen_armadillo.glb'),
                  'skins': ['armadillo_a'],
                  'binding': 'integration/actors.yml (Xeen Sand Worm B), not merged: the parent xeen-s7 merges it'}
d['credits_spent'] = sum(j.get('consumed_credits', 0) for j in d['meshy']['jobs'].values())
d['stage'] = 'installed (xeen-s7-armadillo, 2026-11-21)'
d['status'] = {'stage': 'installed', 'technical': 'complete',
               'agent_visual_review': 'clay clip sheets (quarter, side), textured EEVEE renders at party eye height, '
                                      'review viewer check (8 clip switches, 0 console errors) and shots',
               'in_game_check': 'XD-21 static model spawns of the installed GLB (Standing, wind-up, blow, hunch, Dead, '
                                'forced LOD 2/3), build-xeen, exit 0; bound-actor check by the parent',
               'user_acceptance': 'pending'}
d['next_action'] = {'owner': 'xeen-s7', 'step': 'merge integration/actors.yml (Xeen Sand Worm B), validate the '
                                                'bindings, XD-21 look at the bound actor'}
p.write_text(json.dumps(d, indent=1) + '\n')
print('PROGRESS', d['status']['stage'], 'credits', d['credits_spent'])
