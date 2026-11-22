#!/usr/bin/env python3
"""Record the selected artifacts, gates and state in creature_3d_progress.json (run under the lease:
creature_workspace.py run ... -- python3 scripts/update_progress.py)."""
import json, hashlib, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *p: os.path.join(HERE, *p)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
s = json.load(open(P('creature_3d_progress.json')))
s['scope'] = 'FULL (lane S sub-agent): Killer Sprite design, tiers sprite_a/b/c, install --world xeen; actors.yml binding left to the lane parent (integration/actors.yml)'
s['references_hd'] = {f: sha(P('references_hd', f)) for f in sorted(os.listdir(P('references_hd'))) if f.endswith('.png') and f[0] in '0'}
s['references_hd']['note'] = '00 alpha haze (<16) zeroed, raw kept as 00_three_quarter_raw.png; 00-04 body without wings, 05 the four wings alone'
s['required_components'] = [{'id': 'body', 'artifact_role': 'body', 'required': True, 'state': 'installed'},
                            {'id': 'wings', 'artifact_role': 'wing cards (own mesh, alpha-blended material)', 'required': True, 'state': 'installed in the body GLB'}]
s['corrections'] = [{'job': 'smart_topology_v2', 'cause': 'smart_topology_v1 gave both hands a thumb and three fingers; a second draw of the same master (5 cr) also had four digits and a fragmented hair shell',
                     'resolution': 'v1 kept; a procedural pinky added per hand (scripts/add_pinky.py) before rigging'}]
s['selected'] = {'mesh': 'meshy/smart_topology_v1/model_urls_glb.glb', 'rig_master': 'work/rig_v5.blend',
                 'textured_master': 'work/rig_v6.blend', 'export': 'export/xeen_sprite.glb', 'export_sha256': sha(P('export', 'xeen_sprite.glb')),
                 'installed_source': 'assets_source/worlds/xeen/models/xeen_sprite.glb',
                 'installed_source_sha256': sha(os.path.join(REPO, 'assets_source/worlds/xeen/models/xeen_sprite.glb')),
                 'installed_runtime_sha256': sha(os.path.join(REPO, 'assets_dev/worlds/xeen/models/xeen_sprite.glb')),
                 'binding_block': 'integration/actors.yml'}
s['gates'] = {'G3_frames': 'max frame error 0.0 deg', 'G4_arm_p99_max': 2.23, 'G4_note': 'cast frames 20-27 (both arms raised then forward) 2.13-2.23 at the off-shoulder band in the armpit; elsewhere <= 2.0',
              'G5_hand_stretch_max': 2.32, 'G6_contacts': 'none in any clip (after arm_offset on Fidget L 12 deg, Death R 16 deg)',
              'floor': 'lowest point of each loop and of every action frame on the floor (0.0 cm), corpse 0.0 cm', 'winding': '0 inverted closed parts',
              'texture_quality_body': {'atlas_pct': 66.2, 'density_p50': 1501, 'spread_non_head': '1.0 (head islands x2)', 'fragments_pct': 0.0, 'stretch_p90': 1.2},
              'lod': {'triangles': [8740, 4370, 2185, 1090], 'ladder_step': 'r25_12 accepted', 'scores': {'lod2': [2.5, 6.0], 'lod3': [4.3, 8.2]}},
              'viewer': 'check_viewer.mjs: 3 tiers x 9 clips switched (27), no console errors'}
s['stage'] = 'installed; binding block staged for the lane parent; no in-game run (no monster rows bound yet)'
s['next_action'] = {'owner': 'lane S parent', 'action': 'paste integration/actors.yml into assets_dev/worlds/xeen/models/actors.yml (descriptor names), run the floor audit and in-game checks'}
json.dump(s, open(P('creature_3d_progress.json'), 'w'), indent=1)
print('PROGRESS updated')
