"""Zoomed joint views for (name, side): the side as it meets its most frequent map neighbour (or itself when none),
native (nearest 4x) left vs master right, 3x zoom, 40 master px each side of the joint."""
import sys, json
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/textures_x4')
import tex, os, numpy as np
W = os.environ.get('WORLD', 'mm8')
from PIL import Image, ImageDraw
out = sys.argv[1]; items = [a.split(':') for a in sys.argv[2:]]
st = tex.ledger_state(); t = tex.inventory()
SIDE = {'right': ('u', 'max'), 'left': ('u', 'min'), 'bottom': ('v', 'max'), 'top': ('v', 'min')}
def latest(n):
    rec = st[W + '/' + n]
    if rec.get('status') == 'accepted': return Image.open(tex.ROOT / rec['master']).convert('RGB')
    res = tex.load_json(tex.JOBS / rec['job'] / 'results.json')
    k = max([k for k in res if res[k]['member'] == W + '/' + n and 'candidate' in res[k]], key=lambda k: res[k]['version'])
    return Image.open(tex.ROOT / res[k]['candidate']).convert('RGB')
cells = []
for n, side in items:
    axis, sd = SIDE[side]
    nb = sorted([x for x in t[W + '/' + n].get('neighbors', []) if x['axis'] == axis and x['side'] == sd], key=lambda x: -x.get('count', 1))
    other = nb[0]['id'].split('/')[1] if nb else n
    def joint(get):
        A, B = get(n), get(other)
        if side in ('right', 'bottom'): first, second = A, B
        else: first, second = B, A
        if axis == 'u':
            h = min(first.height, second.height); y0 = h // 2 - 80
            a = first.crop((first.width - 40, y0, first.width, y0 + 160)); b = second.crop((0, y0, 40, y0 + 160))
            im = Image.new('RGB', (80, 160)); im.paste(a, (0, 0)); im.paste(b, (40, 0))
        else:
            w = min(first.width, second.width); x0 = w // 2 - 80
            a = first.crop((x0, first.height - 40, x0 + 160, first.height)); b = second.crop((x0, 0, x0 + 160, 40))
            im = Image.new('RGB', (160, 80)); im.paste(a, (0, 0)); im.paste(b, (0, 40))
        return im.resize((im.width * 3, im.height * 3), Image.NEAREST)
    nat = joint(lambda x: (lambda i: i.resize((i.width * 4, i.height * 4), Image.NEAREST))(tex.open_native(W, x).convert('RGB')))
    mas = joint(latest)
    c = Image.new('RGB', (nat.width * 2 + 8, nat.height + 14)); c.paste(nat, (0, 14)); c.paste(mas, (nat.width + 8, 14))
    ImageDraw.Draw(c).text((2, 1), f'{n} {side} | {other}', fill=(255, 220, 80)); cells.append(c)
cw = max(c.width for c in cells); ch = max(c.height for c in cells); cols = max(1, 1800 // cw)
s = Image.new('RGB', (cw * cols, ch * ((len(cells) + cols - 1) // cols)))
for i, c in enumerate(cells): s.paste(c, ((i % cols) * cw, (i // cols) * ch))
s.save(out); print(s.size)
