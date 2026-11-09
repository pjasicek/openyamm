"""For each name: left neighbour | latest result (any status) | right neighbour (context ids recorded for that version)."""
import sys
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/textures_x4')
import tex, os
W = os.environ.get('WORLD', 'mm8')
from PIL import Image, ImageDraw
out, names = sys.argv[1], sys.argv[2:]
st = tex.ledger_state(); t = tex.inventory()
rows = []
for n in names:
    m = W + '/' + n; rec = st[m]; jd = tex.JOBS / rec['job']
    req = tex.load_json(jd / 'job.json')['requests'][m]; res = tex.load_json(jd / 'results.json', {})
    keys = [k for k in res if res[k]['member'] == m and 'candidate' in res[k]]
    k = max(keys, key=lambda k: res[k]['version']); v = str(res[k]['version'])
    ctx = (req.get('context') or {}).get(v, {})
    imgs = []
    order = ('left', None, 'right') if {'left','right'} & set(ctx) or not ctx else ('top', None, 'bottom')
    for side in order:
        if side is None: imgs.append(Image.open(tex.ROOT / res[k]['candidate']).convert('RGB')); continue
        o = ctx.get(side)
        imgs.append(Image.open(tex.ROOT / st[o]['master']).convert('RGB') if o and st[o].get('master') else Image.new('RGB', (64, 64)))
    h = 300; imgs = [i.resize((max(1, round(i.width * h / i.height)), h)) for i in imgs]
    row = Image.new('RGB', (sum(i.width for i in imgs) + 4, h + 14)); x = 0
    for i in imgs: row.paste(i, (x, 14)); x += i.width + 2
    ImageDraw.Draw(row).text((2, 1), f"{k} ctx={ctx} {'; '.join(res[k]['flags'])}"[:160], fill=(255, 220, 80)); rows.append(row)
W = max(r.width for r in rows); s = Image.new('RGB', (W, sum(r.height for r in rows)))
y = 0
for r in rows: s.paste(r, (0, y)); y += r.height
s.thumbnail((1400, 2400)); s.save(out)
