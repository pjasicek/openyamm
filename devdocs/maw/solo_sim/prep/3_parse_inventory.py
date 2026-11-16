"""Step 3. Parses the inventory logs and tables:
- inv/inventory.json: per difficulty and map, the spawned actors [monster id, HP as spawned];
- inv/inventory_pos.json: the same with positions (x, y, z), for grouping;
- inv/mapmonsters.json: per difficulty, map and monster id, [level, max HP] of MAW's map monster table at zero banks.
An actor whose HP is more than twice its row's is a boss (its HP ratio is kept as the boss multiplier)."""
import re, json, glob, os
from _common import INV

inv = {}; pos = {}
for f in glob.glob(INV + '/inv_*.yml.log'):
    world, dk = re.search(r'inv_(mm\d)_(\w+)\.yml', f).groups()
    cur = None
    for line in open(f, errors='replace'):
        m = re.match(r'^(\S+\.(?:odm|blv)): (\d+) / (\d+) slain, (\d+) left', line)
        if m:
            cur = m.group(1)
            inv.setdefault(dk, {})[cur] = dict(world=world, counted=int(m.group(3)), actors=[])
            pos.setdefault(dk, {})[cur] = []
            continue
        m = re.match(r'^  #(\d+) (.*) \((\d+)\) at (-?\d+) (-?\d+) (-?\d+), \d+ away, hp (\d+)', line)
        if m and cur:
            inv[dk][cur]['actors'].append((int(m.group(3)), int(m.group(7))))
            pos[dk][cur].append(dict(mid=int(m.group(3)), x=int(m.group(4)), y=int(m.group(5)), z=int(m.group(6)),
                                     hp=int(m.group(7))))
json.dump(inv, open(INV + '/inventory.json', 'w'))
json.dump(pos, open(INV + '/inventory_pos.json', 'w'))

mm = {}
for f in glob.glob(INV + '/mm_*_*.tsv'):
    world, dk = re.search(r'mm_(mm\d)_(\w+)\.tsv', f).groups()
    for line in open(f).read().splitlines()[1:]:
        c = line.split('\t')
        mm.setdefault(dk, {}).setdefault(c[1], {})[int(c[4])] = (int(c[6]), int(c[7]))
json.dump(mm, open(INV + '/mapmonsters.json', 'w'))
for dk in sorted(inv):
    print(dk, 'maps', len(inv[dk]), 'actors', sum(len(d['actors']) for d in inv[dk].values()))
