"""Audit of every continuous abutment (neighbors, side max) between accepted masters of a world.

Joint step = mean |colour difference| across the joint at 4x (last column of A vs first of B, colour, per row),
relative to the median interior column step of the two masters; native the same at native scale. Flag when the
master joint is clearly worse than the native joint."""
import sys, json
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/textures_x4')
import tex, numpy as np
from PIL import Image
world = sys.argv[1]
t = tex.inventory(); st = tex.ledger_state()
cache = {}
def master(i):
    if i not in cache: cache[i] = np.asarray(Image.open(tex.ROOT / st[i]['master']).convert('RGB').resize(tuple(t[i]['size']), Image.BOX)).astype(float)
    return cache[i]
def native(i):
    return tex.native_rgba(tex.open_native(world, t[i]['name']))[..., :3].astype(float)
def ratio(a, b, axis):
    # a's high edge meets b's low edge
    if axis == 'v': a, b = a.transpose(1, 0, 2), b.transpose(1, 0, 2)
    h = min(a.shape[0], b.shape[0]); a, b = a[:h], b[:h]
    joint = np.abs(a[:, -1] - b[:, 0]).mean()
    interior = np.median([np.abs(np.diff(x, axis=1)).mean() for x in (a[:, -6:], b[:, :6])]) + 1e-6
    return joint / interior
rows = []
seen = set()
for i, e in t.items():
    if e['world'] != world or st.get(i, {}).get('status') != 'accepted': continue
    for n in e.get('neighbors', []):
        j = n['id']
        if n['side'] != 'max' or st.get(j, {}).get('status') != 'accepted' or (i, j, n['axis']) in seen: continue
        seen.add((i, j, n['axis']))
        if (e.get('assembly') or {}).get('members') and j in e['assembly']['members']: continue
        try:
            rm = ratio(master(i), master(j), n['axis']); rn = ratio(native(i), native(j), n['axis'])
        except Exception as err:
            continue
        rows.append((rm / max(rn, 1.0), rm, rn, i.split('/')[1], j.split('/')[1], n['axis'], n.get('count', 1)))
rows.sort(reverse=True)
bad = [r for r in rows if r[0] > 2.0]
print(f'{len(rows)} joints between accepted {world} masters; {len(bad)} with master step > 2x native')
for r in bad[:60]: print(f'{r[0]:5.1f}  master {r[1]:5.1f} native {r[2]:4.1f}  {r[3]} | {r[4]} ({r[5]}, x{r[6]})')
json.dump([list(r) for r in rows], open(f'./jointsN_{world}.json', 'w'))
