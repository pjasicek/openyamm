"""Label the twelve native tour PNGs; refuse to manufacture a sheet without them."""
from pathlib import Path

from PIL import Image, ImageDraw
import yaml

project = Path(__file__).resolve().parent
tour = yaml.safe_load((project / 'review_tour_01.yml').read_text())
folder = Path(tour['output_dir'])
paths = [folder / f'{i:02d}-{shot["name"]}.png' for i, shot in enumerate(tour['shots'], 1)]
assert len(paths) == 12 and all(p.is_file() for p in paths), 'Capture all twelve native tour views first'
sheet = Image.new('RGB', (1920, 4 * 390), '#15151a')
draw = ImageDraw.Draw(sheet)
for i, (path, shot) in enumerate(zip(paths, tour['shots'])):
    tile = Image.open(path).convert('RGB')
    tile.thumbnail((640, 360))
    x, y = (i % 3) * 640, (i // 3) * 390
    sheet.paste(tile, (x + (640 - tile.width) // 2, y))
    draw.text((x + 12, y + 367), shot['name'], fill='#eee9d9')
sheet.save(folder / 'sheet.jpg', quality=93)
print(folder / 'sheet.jpg')
