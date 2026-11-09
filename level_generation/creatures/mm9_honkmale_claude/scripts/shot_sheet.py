"""Contact sheet of viewer shots. Args: <out png> <columns> <tile px> <name> [...] (names in review/shots/)"""
import sys
from PIL import Image, ImageDraw
out, cols, tile = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); names = sys.argv[4:]
rows = (len(names) + cols - 1) // cols
ims = []
for n in names:
    im = Image.open(f'review/shots/{n}.png').convert('RGB')
    s = min(im.size); l = (im.size[0] - s) // 2; t = (im.size[1] - s) // 2
    ims.append((n, im.crop((l, t, l + s, t + s)).resize((tile, tile), Image.LANCZOS)))
S = Image.new('RGB', (cols * tile, rows * tile), (40, 40, 40))
d = ImageDraw.Draw(S)
for k, (n, im) in enumerate(ims):
    x, y = (k % cols) * tile, (k // cols) * tile
    S.paste(im, (x, y)); d.text((x + 6, y + 4), n, fill=(255, 255, 120))
S.save(out)
