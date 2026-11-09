"""Label every captured tour frame; accepts the native or supplementary preview directory."""
from pathlib import Path
import sys
from PIL import Image, ImageDraw

folder = Path(sys.argv[1])
shots = sorted(folder.glob('[0-9][0-9]-*.png'))
assert len(shots) == 12, f'Expected all twelve tour shots, found {len(shots)}'
preview = folder.name.startswith('blender')
sheet = Image.new('RGB', (1920, 1736), '#17151a')
draw = ImageDraw.Draw(sheet)
draw.text((16, 8), 'D8 | BLENDER GEOMETRY PREVIEW — NOT A GAME CAPTURE' if preview else 'D8 | Native game tour', fill='white')
for index, path in enumerate(shots):
    x, y = index % 3 * 640, 36 + index // 3 * 424
    with Image.open(path) as source:
        frame = source.convert('RGB')
        frame.thumbnail((640, 400))
        sheet.paste(frame, (x, y))
    draw.text((x + 10, y + 402), path.stem.replace('_', ' '), fill='white')
sheet.save(folder / 'sheet.jpg', quality=92)
print(folder / 'sheet.jpg')
