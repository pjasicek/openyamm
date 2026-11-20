"""Step 5. route/route_<dk>.json, the playthrough spec SoloRoute reads, per difficulty:
- maps: file, world, actors [monster id, HP ratio to its row (boss multiplier when > 2), group], chests;
- group: actors within 512 units of each other (z counted twice), union-find over the spawned positions;
- quests: one reward per quest event (the largest AddValue(Experience) inside each evt function of Global.lua and of
  every map script: a quest's branches are alternatives), sorted; SoloRoute pays them smallest first, spread along the
  route by map count. Map-script quests are in this list, so each map's own `quests` is [0, 0];
- seeds 1-5, the level stages of _common.STAGES (1 is the start, before the first map), `pool_per_kind` 40 (the size
  of the short lists SoloRoute keeps per item kind, see its `selectKept`).
The party reference routes (route_<dk>_party.json) are written by 7_party_routes.py after the solo runs.
Variants for the quest check: route_<dk>_one.json (the same list; kept for the comparison runs) and
route_<dk>_none.json (no quests), for nightmare, insanity and madness."""
import json, re, collections, os
from _common import REPO, INV, ROUTE, ROUTE_OPTIONS, STAGES

os.chdir(REPO)
inv = json.load(open(INV + '/inventory_pos.json')); mm = json.load(open(INV + '/mapmonsters.json'))
md = json.load(open(INV + '/mapdata.json')); maps = json.load(open(INV + '/maps.json'))


def scan(path):
    cur = None; ev = collections.OrderedDict()
    for line in open(path, errors='replace').read().splitlines():
        m = re.match(r'^(\w+)\((\d+)', line)
        if m:
            cur = (m.group(1), int(m.group(2))); continue
        x = re.search(r'AddValue\(Experience, *(\d+)\)', line)
        if x and cur is not None:
            ev.setdefault(cur, []).append(int(x.group(1)))
    return ev


quests = [max(v) for v in scan('assets_dev/engine/events/Global.lua').values()]
for f, m in maps.items():
    try:
        quests += [max(v) for v in scan(f'assets_dev/worlds/{m["world"]}/events/maps/{f.rsplit(".", 1)[0]}.lua').values()]
    except FileNotFoundError:
        pass
quests.sort()


def groups(acts, radius=512):
    n = len(acts); parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for i in range(n):
        for j in range(i + 1, n):
            a, b = acts[i], acts[j]
            if (a['x'] - b['x'])**2 + (a['y'] - b['y'])**2 + ((a['z'] - b['z'])*2)**2 < radius*radius:
                parent[find(i)] = find(j)
    roots = {}
    return [roots.setdefault(find(i), len(roots)) for i in range(n)]


for dk, opt in ROUTE_OPTIONS.items():
    route = []
    for f, acts in sorted(inv[dk].items()):
        rows = mm[dk].get(f, {}); g = groups(acts)
        actors = []
        for i, a in enumerate(acts):
            r = rows.get(str(a['mid']))
            actors.append([a['mid'], round(a['hp']/r[1], 2) if r and r[1] > 0 else 1.0, g[i]])
        route.append(dict(file=f, world=maps[f]['world'], actors=actors, chests=md['chests'].get(f, []), quests=[0, 0]))
    spec = dict(options=opt, stages=STAGES, pool_per_kind=40, seeds=[1, 2, 3, 4, 5], maps=route,
                global_quest_values=quests, global_quests=[len(quests), sum(quests)])
    json.dump(spec, open(f'{ROUTE}/route_{dk}.json', 'w'))
    if dk in ('nightmare', 'insanity', 'madness'):
        json.dump(spec, open(f'{ROUTE}/route_{dk}_one.json', 'w'))
        json.dump(dict(spec, global_quest_values=[0], global_quests=[0.0001, 1]), open(f'{ROUTE}/route_{dk}_none.json', 'w'))
print('routes written;', len(quests), 'quest rewards,', sum(quests), 'experience')
