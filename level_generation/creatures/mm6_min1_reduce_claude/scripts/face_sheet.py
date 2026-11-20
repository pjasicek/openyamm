"""Contact sheets of face_views.py renders: one row per label. Usage: face_sheet.py <out.png> <shots,...> <label> ..."""
import sys
from PIL import Image
out, shots, labels = sys.argv[1], sys.argv[2].split(','), sys.argv[3:]
s = Image.new('RGB', (400 * len(shots), 400 * len(labels)))
for j, t in enumerate(labels):
    for i, k in enumerate(shots):
        s.paste(Image.open(f'review/faces/{t}_{k}.png').convert('RGB').resize((400, 400)), (i * 400, j * 400))
s.save(out)
