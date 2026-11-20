"""rv.py JOB [NAME_vN ...] -> scratch rv_<job>_<k>.png sheets (6 rows each): native | x4 | 2x2 tile | u joint | v joint
for the latest candidate of every not-yet-accepted member (or the given candidates)."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/textures_x4')
import tex
J = tex.JOBS / sys.argv[1]
OUT = Path(sys.argv[0]).resolve().parent / 'sheets'; OUT.mkdir(exist_ok=True)
P = 240
st = tex.ledger_state()
res = json.load(open(J / 'results.json'))
if len(sys.argv) > 2:
    cands = sys.argv[2:]
else:
    latest = {}
    for k, v in res.items():
        if st.get(v['member'], {}).get('status') == 'accepted' or not (J / 'candidates' / f'{k}.png').exists():
            continue
        if '_v' not in k: continue
        n, ver = k.rsplit('_v', 1)
        if ver.isdigit() and int(ver) >= latest.get(n, (0,))[0]:
            latest[n] = (int(ver), k)
    cands = [v[1] for v in latest.values()]
def fit(im, s=P):
    r = min(s / im.width, s / im.height); return im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))))
rows = []
for cand in cands:
    img = Image.open(J / 'candidates' / f'{cand}.png').convert('RGB')
    nat = Image.open(J / 'review' / f'native_{cand.rsplit("_v",1)[0]}.png').convert('RGB').resize(img.size, Image.NEAREST)
    w, h = img.size
    t = Image.new('RGB', (w * 2, h * 2))
    for dx in (0, w):
        for dy in (0, h): t.paste(img, (dx, dy))
    s = min(w, h, 384)
    u = t.crop((w - s // 2, h // 2 - s // 2, w + s // 2, h // 2 + s // 2))
    v = t.crop((w // 2 - s // 2, h - s // 2, w // 2 + s // 2, h + s // 2))
    panels = [fit(nat), fit(img), fit(t), u.resize((P, P)), v.resize((P, P))]
    row = Image.new('RGB', (5 * (P + 6), P + 16), (24, 24, 24))
    for i, p in enumerate(panels): row.paste(p, (i * (P + 6), 16))
    flags = res.get(cand, {}).get('flags')
    ImageDraw.Draw(row).text((3, 2), f'{cand} {flags}', fill=(255, 220, 0))
    rows.append(row)
for k in range(0, len(rows), 6):
    chunk = rows[k:k + 6]
    sheet = Image.new('RGB', (chunk[0].width, sum(r.height for r in chunk)))
    y = 0
    for r in chunk: sheet.paste(r, (0, y)); y += r.height
    path = OUT / f'rv_{sys.argv[1][-14:]}_{k // 6}.png'; sheet.save(path); print(path)
