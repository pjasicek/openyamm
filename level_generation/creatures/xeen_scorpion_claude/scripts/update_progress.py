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
d['references_hd']['gate'] = ('Claude gate 2026-11-20 (work/masters_gate.png): identity, palette, two arms with one hook '
                              'each, four legs and feet, side views face correctly, 1536x1024 true alpha')
d['required_components'] = [{'id': 'body', 'artifact_role': 'body', 'required': True,
                             'note': 'one mesh of 56 rigid chitin pieces (Smart Topology): head, eyes, radial mouth beads, '
                                     'antennae, thorax, abdomen, two raptorial arms with hooks, four legs'}]
d['installed'] = {'source': 'assets_source/worlds/xeen/models/xeen_mantis.glb',
                  'sha256': sha(REPO / 'assets_source/worlds/xeen/models/xeen_mantis.glb'),
                  'runtime_sha256': sha(REPO / 'assets_dev/worlds/xeen/models/xeen_mantis.glb'),
                  'skins': ['mantis_a', 'mantis_b', 'mantis_c', 'mantis_lava'],
                  'binding': 'integration/actors.yml (Xeen Mantis A/B/C, Xeen Crawler C), not merged: the parent '
                             'xeen-s5 merges it'}
d['status'] = {'stage': 'installed', 'technical': 'complete',
               'agent_visual_review': 'clay clip sheets, attack/death frame renders, textured EEVEE renders at party eye '
                                      'height (every skin, the blow, the corpse, the face), review viewer check (32 '
                                      'switches, 0 errors) and shots',
               'in_game_check': 'XD-21 static model spawns of the installed GLB (Standing, wind-up, blow, Dead, Queen '
                                'scale, forced LOD 2/3; default skin mantis_a only), build-xeen of 2026-11-20 18:28, '
                                'exit 0; bound-actor check of the other skins and the lava glow by the parent',
               'user_acceptance': 'pending',
               'next_action': {'owner': 'xeen-s5', 'action': 'merge integration/actors.yml, headless-validate, '
                                                             'XD-21 tour with Xeen Mantis A/B/C and Xeen Crawler C'}}
p.write_text(json.dumps(d, indent=1) + '\n')
print('PROGRESS', d['status']['stage'])
