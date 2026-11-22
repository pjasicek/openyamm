#!/usr/bin/env python3
"""Write the non-Meshy fields of creature_3d_progress.json (run under the lease: creature_workspace.py run)."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
p = ROOT / 'creature_3d_progress.json'
d = json.loads(p.read_text())
sha = lambda f: hashlib.sha256(Path(f).read_bytes()).hexdigest()
d['references_hd'] = {f.name: sha(f) for f in sorted((ROOT / 'references_hd').glob('0*.png'))}
d['required_components'] = [{'id': 'body', 'artifact_role': 'body', 'required': True,
                             'note': 'one mesh: body, head, snout, clawed hands, eyeballs, hind toe claws, procedural tail'}]
d['installed'] = {'source': 'assets_source/worlds/xeen/models/xeen_mole.glb',
                  'sha256': sha(REPO / 'assets_source/worlds/xeen/models/xeen_mole.glb'),
                  'runtime_sha256': sha(REPO / 'assets_dev/worlds/xeen/models/xeen_mole.glb'),
                  'skins': ['mole_a', 'mole_b', 'mole_c'],
                  'binding': 'integration/actors.yml (Xeen Mole A/B/C), not merged: the parent xeen-s3 merges it'}
d['status'] = {'stage': 'installed', 'technical': 'complete',
               'agent_visual_review': 'clay clip sheets, stress poses, textured EEVEE renders at party eye height, '
                                      'tier renders, review viewer check (24 switches, 0 errors) and shots',
               'in_game_check': 'XD-21 static model spawns of the installed GLB (Standing, wind-up, blow, Dead, '
                                'forced LOD 2/3), build-xeen 2026-11-20 17:10, exit 0; bound-actor check by the parent',
               'user_acceptance': 'pending',
               'next_action': {'owner': 'xeen-s3', 'action': 'merge integration/actors.yml, headless-validate, '
                                                             'XD-21 tour with Xeen Mole A/B/C'}}
p.write_text(json.dumps(d, indent=1) + '\n')
print('PROGRESS', d['status']['stage'])
