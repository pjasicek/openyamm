"""Side-by-side review sheets: original | candidate for each shot name."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
a, b, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
for left in sorted(a.glob('*.png')):
    right = b / left.name
    if not right.exists():
        continue
    L, R = Image.open(left).convert('RGB'), Image.open(right).convert('RGB')
    w, h = L.size
    sheet = Image.new('RGB', (w * 2 + 8, h), (0, 0, 0))
    sheet.paste(L, (0, 0)); sheet.paste(R, (w + 8, 0))
    d = ImageDraw.Draw(sheet)
    for x, label in ((10, a.name), (w + 18, b.name)):
        d.rectangle([x - 4, 70, x + 220, 110], fill=(0, 0, 0)); d.text((x, 76), label, fill=(255, 255, 0), font_size=28)
    sheet.resize((w, h // 2)).save(out / (left.stem + '.jpg'), quality=88)
