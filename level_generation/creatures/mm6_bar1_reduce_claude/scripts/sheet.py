"""Contact sheet of close renders: rows = labels, columns = spot_view pairs.
Usage: sheet.py <out.png> <label,label,...> <spot_view,spot_view,...> [cell px]"""
import sys
from PIL import Image
out, labels, cols = sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(',')
c = int(sys.argv[4]) if len(sys.argv) > 4 else 360
s = Image.new('RGB', (c * len(cols), c * len(labels)))
for j, t in enumerate(labels):
    for i, sv in enumerate(cols):
        s.paste(Image.open(f'review/close/{t}_{sv}.png').convert('RGB').resize((c, c)), (i * c, j * c))
s.save(out)
