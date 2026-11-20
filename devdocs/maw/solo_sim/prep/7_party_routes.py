"""Step 7 (after the solo route runs). route/route_<dk>_party.json: the same route for a party of five, the reference
the solo run is compared against. Its snapshots are taken at the numbers of cleared maps where the solo run reached
its level stages (the median over the seeds of route/out_<dk>.jsonl), so "stage 200" is the same place of the game for
both; the end snapshot (stage 0) is written by every run."""
import json, statistics, collections
from _common import ROUTE, ROUTE_OPTIONS

for dk in ROUTE_OPTIONS:
    spec = json.load(open(f'{ROUTE}/route_{dk}.json'))
    maps = collections.defaultdict(list)
    for line in open(f'{ROUTE}/out_{dk}.jsonl'):
        d = json.loads(line)
        if d['kind'] == 'snapshot' and d['stage'] > 0:
            maps[d['stage']].append(d['maps_cleared'])
    stage_maps = [[stage, round(statistics.median(v))] for stage, v in sorted(maps.items()) if len(v) >= 3]
    json.dump(dict(spec, party_count=5, stage_maps=stage_maps), open(f'{ROUTE}/route_{dk}_party.json', 'w'))
    print(dk, stage_maps)
