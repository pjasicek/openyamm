"""Low-frequency tone steps at map joints: per row, the mean colour of 3 native-px columns each side of the joint
(masters BOX-reduced to native size). A joint is flagged where the master's per-row step exceeds the native's by
more than THRESH over most of its rows: brightness or colour that jumps across a wall where the original continues.
usage: WORLD=mm8 python3 audit/tone.py [THRESH]"""
import sys, os, json
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/textures_x4')
import tex, numpy as np
from PIL import Image
from scipy import ndimage
W = os.environ.get('WORLD', 'mm8'); TH = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
st = tex.ledger_state(); t = tex.inventory(); M, N = {}, {}
def master(i):
    if i not in M:
        a = np.asarray(Image.open(tex.ROOT / st[i]['master']).convert('RGB').resize(tuple(t[i]['size']), Image.BOX)).astype(float)
        M[i] = ndimage.gaussian_filter(a, (6, 2, 0))
    return M[i]
def native(i):
    if i not in N: N[i] = ndimage.gaussian_filter(tex.native_rgba(tex.open_native(W, t[i]['name'])).astype(float)[..., :3], (6, 2, 0))
    return N[i]
rows = []
seen = set()
for i, e in t.items():
    if e['world'] != W or st.get(i, {}).get('status') != 'accepted': continue
    for nb in e.get('neighbors', []):
        j = nb['id']
        if nb['side'] != 'max' or st.get(j, {}).get('status') != 'accepted' or (i, j, nb['axis']) in seen: continue
        seen.add((i, j, nb['axis']))
        a, b, na, nbn = master(i), master(j), native(i), native(j)
        if nb['axis'] == 'v': a, b, na, nbn = (x.transpose(1, 0, 2) for x in (a, b, na, nbn))
        # (smoothing above is along rows (axis 0) for u joints; recompute for v)

        h = min(a.shape[0], b.shape[0], na.shape[0], nbn.shape[0])
        dm = np.abs(a[:h, -6:].mean(1) - b[:h, :6].mean(1)).mean(1)
        dn = np.abs(na[:h, -6:].mean(1) - nbn[:h, :6].mean(1)).mean(1)
        excess = dm - dn
        frac = (excess > TH).mean()
        if frac > 0.4:
            rows.append((round(float(np.median(excess)), 1), round(float(frac), 2), i.split('/')[1], j.split('/')[1], nb['axis'], nb.get('count', 1)))
rows.sort(reverse=True)
print(len(rows), 'joints with a tone step >', TH, 'over >40% of the joint')
for r in rows: print(*r)
json.dump(rows, open(f'./tone_{W}.json', 'w'))
