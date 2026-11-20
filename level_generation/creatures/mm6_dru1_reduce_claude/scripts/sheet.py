"""Contact sheet: rows = labels, columns = spot_view pairs. Usage: sheet.py <out.png> <labels,...> <spot_view,...>"""
import sys
from PIL import Image
out, labels, cols = sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(',')
S = 360; s = Image.new('RGB', (S * len(cols), S * len(labels)))
for j, t in enumerate(labels):
    for i, c in enumerate(cols):
        s.paste(Image.open(f'review/close/{t}_{c}.png').convert('RGB').resize((S, S)), (i * S, j * S))
s.save(out)
