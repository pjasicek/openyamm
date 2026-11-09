"""Stack rows of images: row_sheet.py out.png 'a_0.png,a_1.png,...' 'b_0.png,...' (each row one comma list)."""
import sys
from PIL import Image
rows = [[Image.open(f).convert('RGB') for f in r.split(',')] for r in sys.argv[2:]]
W = max(sum(i.width for i in r) for r in rows); H = sum(max(i.height for i in r) for r in rows)
S = Image.new('RGB', (W, H), (40, 40, 40)); y = 0
for r in rows:
    x = 0
    for i in r: S.paste(i, (x, y)); x += i.width
    y += max(i.height for i in r)
S.save(sys.argv[1])
