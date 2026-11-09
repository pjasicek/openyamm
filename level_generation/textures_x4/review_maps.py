"""Exact minimum set of maps whose faces show every in-scope texture of one world (scipy MILP set cover)."""
import json, sys
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
world = sys.argv[1]
root = str(__import__('pathlib').Path(__file__).resolve().parents[2]) + '/'
textures = json.load(open(root + 'level_generation/textures_x4/inventory.json'))['textures']
names = {}
for row in open(root + 'assets_dev/engine/data_tables/map_stats.txt', encoding='latin-1'):
    f = row.split('\t')
    if len(f) > 2 and f[0].isdigit():
        names.setdefault(f[2].lower(), f[1])
U = [x for x in textures if x['world'] == world and not x.get('exclude')]
maps = sorted({m for x in U for m in x['maps']})
A = np.array([[1 if m in x['maps'] else 0 for m in maps] for x in U])
res = milp(c=np.ones(len(maps)), integrality=np.ones(len(maps)), bounds=Bounds(0, 1),
           constraints=LinearConstraint(A, lb=1))
chosen = [m for m, v in zip(maps, res.x) if v > 0.5]
print(f'| Map | Name | Textures | Only here | Event-switched |')
print('| --- | --- | ---: | ---: | --- |')
for m in sorted(chosen, key=lambda m: (m.endswith('.blv'), m)):
    here = [x for x in U if m in x['maps']]
    only = [x for x in here if len(set(x['maps']) & set(chosen)) == 1]
    ev = [x['name'] for x in only if x.get('event_switched')]
    print(f"| `{m}` | {names.get(m, '?')} | {len(here)} | {len(only)} | {' '.join(ev) or '-'} |")
print(f'\n{len(U)} textures, {len(maps)} maps use them, minimum cover {len(chosen)} maps')
