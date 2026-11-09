"""Contact sheet of close_views.py renders: one row per label. Usage: close_sheet.py <out.png> <spot_view,...> <label> ..."""
import sys
from PIL import Image, ImageDraw
out, shots, labels = sys.argv[1], sys.argv[2].split(','), sys.argv[3:]
S = 360
s = Image.new('RGB', (S * len(shots), S * len(labels)))
for j, t in enumerate(labels):
    for i, k in enumerate(shots):
        s.paste(Image.open(f'review/close/{t}_{k}.png').convert('RGB').resize((S, S)), (i * S, j * S))
    ImageDraw.Draw(s).text((6, j * S + 6), t, fill=(255, 255, 0))
s.save(out)
