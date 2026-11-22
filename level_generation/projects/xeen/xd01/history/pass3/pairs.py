import sys, glob, os
from PIL import Image, ImageDraw
X = os.path.dirname(os.path.realpath(__file__))
def key(f): return os.path.basename(f).split('-', 1)[1]
before = {key(f): f for f in glob.glob(f'{X}/shots_before/*.png')}
after = sorted(glob.glob(f'{X}/shots_after/*.png'))
W, H = 560, 315
rows = []
for f in after:
    k = key(f)
    b = before.get(k)
    row = Image.new('RGB', (2 * W + 10, H + 18), 'black')
    d = ImageDraw.Draw(row)
    if b: row.paste(Image.open(b).convert('RGB').resize((W, H)), (0, 18))
    row.paste(Image.open(f).convert('RGB').resize((W, H)), (W + 10, 18))
    d.text((4, 2), 'before ' + k if b else '(no before) ' + k, fill='white'); d.text((W + 14, 2), 'after ' + k, fill='white')
    rows.append(row)
n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
for i in range(0, len(rows), n):
    part = rows[i:i + n]
    sheet = Image.new('RGB', (part[0].width, sum(r.height for r in part)))
    y = 0
    for r in part: sheet.paste(r, (0, y)); y += r.height
    sheet.save(f'{X}/pairs_{i // n + 1}.jpg', quality=85)
print(len(rows))
