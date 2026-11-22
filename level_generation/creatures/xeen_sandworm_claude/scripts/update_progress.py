#!/usr/bin/env python3
"""Write the finished state into creature_3d_progress.json (run under the lease:
python3 tools/creature_workspace.py run --project <P> --token <T> -- python3 <P>/scripts/update_progress.py <P>)."""
import json, hashlib, sys
p = sys.argv[1]
d = json.load(open(p + '/creature_3d_progress.json'))
sha = lambda f: hashlib.sha256(open(f, 'rb').read()).hexdigest()
d['stage'] = 'installed; binding block ready (not merged); not accepted by the user'
d['installed'] = {'source': 'assets_source/worlds/xeen/models/xeen_sandworm.glb',
                  'sha256': sha('assets_source/worlds/xeen/models/xeen_sandworm.glb'),
                  'runtime': 'assets_dev/worlds/xeen/models/xeen_sandworm.glb'}
d['binding_block'] = p + '/integration/actors.yml'
d['skins'] = {'sandworm_a': 'Xeen Sand Worm A, scale 110', 'sandworm_c': 'Xeen Sand Worm C, scale 126.5'}
d['clips'] = json.load(open(p + '/work/anim_info.json'))['clips']
for c in d['clips'].values():
    c.pop('maw_y', None); c.pop('maw_z', None)
d['texture_quality'] = {'atlas_pct': 76.5, 'density_p10_p50_p90': [796, 902, 1297], 'spread': 1.63, 'islands': 95,
                        'fragments_pct': 0.0, 'stretch_p90': 1.14}
d['lods'] = [8396, 4197, 2096, 1030]
d['next_action'] = {'owner': 'parent xeen-s6',
                    'what': 'merge integration/actors.yml (Xeen Sand Worm A and C), run the binding validation, '
                            'look at both skins in game'}
json.dump(d, open(p + '/creature_3d_progress.json', 'w'), indent=1)
print('PROGRESS updated')
