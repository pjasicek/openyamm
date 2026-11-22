#!/usr/bin/env python3
"""Write the finished state into creature_3d_progress.json (run under the lease:
python3 tools/creature_workspace.py run --project <P> --token <T> -- python3 <P>/scripts/update_progress.py <P>)."""
import json, hashlib, sys
p = sys.argv[1]
d = json.load(open(p + '/creature_3d_progress.json'))
sha = lambda f: hashlib.sha256(open(f, 'rb').read()).hexdigest()
d['stage'] = 'installed; binding block ready (not merged); not accepted by the user'
d['installed'] = {'source': 'assets_source/worlds/xeen/models/xeen_octopod.glb',
                  'sha256': sha('assets_source/worlds/xeen/models/xeen_octopod.glb'),
                  'runtime': 'assets_dev/worlds/xeen/models/xeen_octopod.glb',
                  'runtime_sha256': sha('assets_dev/worlds/xeen/models/xeen_octopod.glb')}
d['binding_block'] = p + '/integration/actors.yml'
d['skins'] = {'octopod_a': 'Xeen Octopod A (135) and D (135, same model, DD-14)', 'octopod_b': 'Xeen Octopod B, 155.25',
              'octopod_c': 'Xeen Octopod C, 175.5'}
d['origin'] = ('waterline: outdoor swimmers are held at the water tile terrain height (= drawn surface); DD-14 cistern '
               'water is the opaque fluid floor face at -736 the actors stand on: no grounded copy, no z_offset')
d['clips'] = json.load(open(p + '/work/anim_info.json'))['clips']
d['texture_quality'] = {'atlas_pct': 74.1, 'density_p10_p50_p90': [1548, 1653, 1796], 'spread': 1.16, 'islands': 185,
                        'fragments_pct': 0.8, 'stretch_p90': 1.29}
d['lods'] = [9587, 4792, 1689, 462]
d['next_action'] = {'owner': 'parent xeen-s7',
                    'what': 'merge integration/actors.yml (Xeen Octopod A/B/C/D), run the binding validation, consider '
                            'the recommended collision sizes; A8 swaps DD-14 actors to 11473'}
json.dump(d, open(p + '/creature_3d_progress.json', 'w'), indent=1)
print('PROGRESS updated')
