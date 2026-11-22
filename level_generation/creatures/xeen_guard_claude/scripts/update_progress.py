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
                             'note': 'one mesh of rigid chrome plates (one bone each: pauldrons on the clavicles, '
                                     'dome and gem on B_Head), dark joint spheres; red gem emission'}]
d['installed'] = {'source': 'assets_source/worlds/xeen/models/xeen_guard.glb',
                  'sha256': sha(REPO / 'assets_source/worlds/xeen/models/xeen_guard.glb'),
                  'runtime_sha256': sha(REPO / 'assets_dev/worlds/xeen/models/xeen_guard.glb'),
                  'skins': ['guard_a'],
                  'binding': 'integration/actors.yml (Xeen Construct D), not merged: the parent xeen-s7 merges it'}
d['credits_spent'] = sum(j.get('consumed_credits', 0) for j in d['meshy']['jobs'].values())
d['stage'] = 'installed (xeen-s7-guard, 2026-11-21)'
d['status'] = {'stage': 'installed', 'technical': 'complete',
               'agent_visual_review': 'clay clip sheets (quarter, side), textured EEVEE renders at party eye height, '
                                      'review viewer check (8 clip switches, 0 console errors) and shots',
               'in_game_check': 'XD-21 static model spawns of the installed GLB (Standing, blow, wind-up, Dead, walk, '
                                'forced LOD 2/3), build-xeen, exit 0; bound-actor check by the parent',
               'user_acceptance': 'pending'}
d['next_action'] = {'owner': 'xeen-s7', 'step': 'merge integration/actors.yml (Xeen Construct D, replaces the '
                                                'mm8_m592 stand-in), validate the bindings, XD-19 look at the bound actor'}
p.write_text(json.dumps(d, indent=1) + '\n')
print('PROGRESS', d['status']['stage'], 'credits', d['credits_spent'])
