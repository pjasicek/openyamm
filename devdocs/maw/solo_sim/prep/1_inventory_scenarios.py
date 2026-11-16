"""Step 1. inv/maps.json (every MM6-MM8 map with its MAW level bands, from tools/maw_site/world_maps.py) and one
headless scenario per world and difficulty (inv/inv_<world>_<dk>.yml). Each scenario starts a one-member MAW game,
zeroes the level banks, dumps the map monster table (`ruleset mapmonsters`, mm_<world>_<dk>.tsv) and loads every map
of its world (arenas left out), listing every spawned actor (`actor remaining`): id, position, HP as spawned, so
MAW's density, bosses and uniques on that difficulty are in the log."""
import json, os, sys
from _common import REPO, INV, DIFFS

sys.path.insert(0, os.path.join(REPO, 'tools', 'maw_site'))
sys.path.insert(0, os.path.join(REPO, 'tools'))
os.chdir(REPO)
import world_maps as wm, yaml

maps = wm.load_maps()
levels = yaml.safe_load((wm.MAW_DATA / 'map_levels.yml').read_text())
out = {}
for f, m in maps.items():
    m['levels'] = wm.map_levels(f, levels)
    out[f] = m
json.dump(out, open(os.path.join(INV, 'maps.json'), 'w'), indent=0)

START = {'mm6': 'oute3.odm', 'mm7': '7out01.odm', 'mm8': 'out01.odm'}
n = 0
for world in ('mm6', 'mm7', 'mm8'):
    files = sorted(f for f, m in out.items() if m['world'] == world and m['levels'] and not m['levels'].get('arena'))
    for dk, rs in DIFFS:
        lines = [f'id: inv_{world}_{dk}', 'title: inventory', 'world: ' + world, 'mode: faithful', 'tags: [measurement]',
                 'steps:', '  - new_game_flow:', f'      start_map: {START[world]}', '      member_count: 1',
                 f'      ruleset: {rs}', '  - console: {line: "ruleset banks 0 0 0 0"}',
                 f'  - console: {{line: "ruleset mapmonsters {INV}/mm_{world}_{dk}.tsv"}}']
        for f in files:
            lines += [f'  - load_map: {{map: {f}}}', '  - console: {line: "actor remaining"}']
        open(os.path.join(INV, f'inv_{world}_{dk}.yml'), 'w').write('\n'.join(lines) + '\n')
        n += 1
print(n, 'scenarios', {w: sum(1 for m in out.values() if m['world'] == w and m['levels']) for w in ('mm6', 'mm7', 'mm8')})
