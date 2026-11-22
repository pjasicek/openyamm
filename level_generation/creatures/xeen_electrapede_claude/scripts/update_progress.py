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
                             'note': 'one mesh: Meshy plates and head (two merged plates rebuilt from neighbours, head 1.25x), '
                                     'two compound-eye ellipsoids, 30 procedural jointed legs'}]
d['installed'] = {'source': 'assets_source/worlds/xeen/models/xeen_electrapede.glb',
                  'sha256': sha(REPO / 'assets_source/worlds/xeen/models/xeen_electrapede.glb'),
                  'runtime_sha256': sha(REPO / 'assets_dev/worlds/xeen/models/xeen_electrapede.glb'),
                  'skins': ['electrapede_a'],
                  'binding': 'integration/actors.yml (Xeen Crawler B), not merged: the parent xeen-s5 merges it'}
d['stage'] = 'installed'
d['status'] = {'stage': 'installed', 'technical': 'complete',
               'agent_visual_review': 'clay clip sheets (quarter, top, front-quarter), textured EEVEE renders at party eye '
                                      'height, review viewer check (8 clips, 0 errors) and shots',
               'in_game_check': 'XD-21 static model spawns of the installed GLB (Standing, bite, wind-up, Walking, Dead, '
                                'forced LOD 2/3), build-xeen; bound-actor check (melee glow) by the parent',
               'user_acceptance': 'pending',
               'next_action': {'owner': 'xeen-s5', 'action': 'merge integration/actors.yml, validate the bindings, '
                                                             'D1 / DD-10A look with Xeen Crawler B'}}
p.write_text(json.dumps(d, indent=1) + '\n')
print('PROGRESS', d['status']['stage'])
