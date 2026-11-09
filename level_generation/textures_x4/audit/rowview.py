"""Facade row as mapped: name[u0:u1] pieces side by side, native (nearest 4x) above, masters below."""
import sys, re, os
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/textures_x4')
import tex
from PIL import Image
W = os.environ.get('WORLD', 'mm8')
out, parts = sys.argv[1], sys.argv[2:]
st = tex.ledger_state()
seq = [(m.group(1), int(m.group(2)), int(m.group(3))) for p in parts for m in [re.match(r'([\w-]+)\[(\d+):(\d+)\]', p)]]
def row(get):
    ims = [get(n).crop((a * 4, 0, b * 4, get(n).height)) for n, a, b in seq]
    h = max(i.height for i in ims); im = Image.new('RGB', (sum(i.width for i in ims), h)); x = 0
    for i in ims: im.paste(i, (x, 0)); x += i.width
    return im
nat = row(lambda n: (lambda i: i.resize((i.width * 4, i.height * 4), Image.NEAREST))(tex.open_native(W, n).convert('RGB')))
def latest(n):
    rec = st[f'{W}/{n}']
    if rec.get('status') == 'accepted': return Image.open(tex.ROOT / rec['master']).convert('RGB')
    res = tex.load_json(tex.JOBS / rec['job'] / 'results.json')
    k = max([k for k in res if res[k]['member'] == f'{W}/{n}' and 'candidate' in res[k]], key=lambda k: res[k]['version'])
    return Image.open(tex.ROOT / res[k]['candidate']).convert('RGB')
mas = row(latest)
s = Image.new('RGB', (nat.width, nat.height * 2 + 10)); s.paste(nat, (0, 0)); s.paste(mas, (0, nat.height + 10))
s.thumbnail((1800, 1400)); s.save(out); print(s.size)
