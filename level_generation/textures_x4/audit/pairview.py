"""Pairs A|B as they abut (axis u: side by side, v: A above B), native (top/left) vs masters, cropped near joint."""
import sys
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/textures_x4')
import tex, os
W = os.environ.get('WORLD', 'mm8')
from PIL import Image, ImageDraw
out = sys.argv[1]; pairs = [p.split(':') for p in sys.argv[2:]]
st = tex.ledger_state()
cells = []
for a, b, axis in pairs:
    def pair(get):
        A, B = get(a), get(b)
        if axis == 'u':
            h = min(A.height, B.height); im = Image.new('RGB', (A.width + B.width, h)); im.paste(A, (0, 0)); im.paste(B, (A.width, 0))
        else:
            w = min(A.width, B.width); im = Image.new('RGB', (w, A.height + B.height)); im.paste(A, (0, 0)); im.paste(B, (0, A.height))
        return im
    nat = pair(lambda n: (lambda i: i.resize((i.width * 4, i.height * 4), Image.NEAREST))(tex.open_native(W, n).convert('RGB')))
    mas = pair(lambda n: Image.open(tex.ROOT / st[W + '/' + n]['master']).convert('RGB'))
    s = 280
    nat.thumbnail((s, s)); mas.thumbnail((s, s))
    c = Image.new('RGB', (2 * s + 10, s + 14)); c.paste(nat, (0, 14)); c.paste(mas, (s + 10, 14))
    ImageDraw.Draw(c).text((2, 1), f'{a}|{b} {axis}', fill=(255, 220, 80)); cells.append(c)
cols = 3; W = cells[0].width; H = cells[0].height
sheet = Image.new('RGB', (W * cols, H * ((len(cells) + cols - 1) // cols)))
for i, c in enumerate(cells): sheet.paste(c, ((i % cols) * W, (i // cols) * H))
sheet.save(out)
