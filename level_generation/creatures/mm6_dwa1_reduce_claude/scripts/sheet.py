"""Close-render sheet: rows = labels, columns = spot_view pairs. Usage: sheet.py <out.png> <spot_view,...> <label> ..."""
import sys
from PIL import Image, ImageDraw
out, cols, labels = sys.argv[1], sys.argv[2].split(','), sys.argv[3:]
S = 360; im = Image.new('RGB', (S * len(cols), (S + 20) * len(labels)), (20, 20, 20)); d = ImageDraw.Draw(im)
for r, l in enumerate(labels):
    d.text((4, r * (S + 20) + 4), l, fill=(255, 230, 120))
    for c, sv in enumerate(cols):
        im.paste(Image.open(f'review/close/{l}_{sv}.png').convert('RGB').resize((S, S)), (c * S, r * (S + 20) + 20))
im.save(out)
