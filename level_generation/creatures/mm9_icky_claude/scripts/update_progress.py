#!/usr/bin/env python3
"""Merge the production record into creature_3d_progress.json (keeps the Meshy receipts). Usage: update_progress.py [ingame.json]"""
import hashlib, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
p = HERE / 'creature_3d_progress.json'
d = json.loads(p.read_text())
sha = lambda f: hashlib.sha256(Path(f).read_bytes()).hexdigest()
clips = json.loads((HERE / 'work' / 'clips_v2.json').read_text())
d.update({
    'creature': 'MM9 Icky family: Airborne Icky (9087, MM9 Icky A), Flying Icky (9088, MM9 Icky B), Astral Icky (9089, MM9 Icky C); one skin FLYINGICKY',
    'identity': 'mm9:icky',
    'scope': 'FULL: HD masters, Meshy Smart Topology + retexture, MM9 skeleton/clip reuse, own wings from the HD top view, LODs, install (mm9 world), bindings, checks',
    'last_update': '2026-10-30',
    'references_hd': {f: sha(HERE / 'references_hd' / f) for f in ('00_three_quarter.png', '01_front.png', '02_back.png', '03_left.png', '04_right.png', '05_wings_top.png')},
    'references_hd_gate': '00-05 accepted (lamprey mouth ring with teeth, horn ears, red eyes, spine spikes, wrist claws, tail barbs and spade, correct left/right); 00 shows one leg, the fit mirrors the full right half. Faint alpha halo clipped (alpha < 40), raw returns kept as *_raw.png.',
    'required_components': [{'id': 'body', 'artifact_role': 'body', 'required': True, 'state': 'installed'},
                            {'id': 'wings', 'artifact_role': 'body (own closed leaves from 05_wings_top, joined into the body mesh)', 'required': True, 'state': 'installed'}],
    'selected': {'meshy_model': 'meshy/icky_smart_v1/model_urls_glb.glb', 'retexture': 'meshy/icky_retexture_v1/',
                 'animated_master': 'work/anim_v2.blend', 'export_lod0': 'export/mm9_icky_lod0.glb',
                 'runtime': {'path': 'export/mm9_icky.glb', 'sha256': sha(HERE / 'export' / 'mm9_icky.glb')}},
    'installed': {'source': 'assets_source/worlds/mm9/models/mm9_icky.glb',
                  'source_sha256': sha(ROOT / 'assets_source/worlds/mm9/models/mm9_icky.glb'),
                  'runtime': 'assets_dev/worlds/mm9/models/mm9_icky.glb (cooked)',
                  'binding': 'assets_dev/worlds/mm9/models/actors.yml: MM9 Icky A/B/C scale 50/100/200 (MONSTERS.txt Scale 0.5/1/2), one skin'},
    'triangles': [5445, 2721, 970, 313],
    'clips': clips['clips'],
    'events': {'attack_melee': 0.293, 'attack_ranged': 0.675, 'cast': {'impact': 0.6, 'release': 'mouth'}},
    'checks': {'viewer': 'run_creature_review.py check: 10 clips, 0 console errors', 'gates': 'review/gates.json, loop seams 0',
               'floor_audit': 'mm9 17/17 ok', 'regression': 'mm9_actor_models_build_every_binding: 17 descriptors on 8 models, 0 failed',
               'winding': '0 inverted closed parts'},
    'artistic_acceptance': 'not recorded',
})
d['meshy']['spent'] = 15
if len(sys.argv) > 1:
    d['checks']['in_game'] = json.loads(Path(sys.argv[1]).read_text())
d['next_action'] = {'owner': 'user', 'action': 'artistic review (viewer, in-game captures)'}
p.write_text(json.dumps(d, indent=1))
print('progress updated')
