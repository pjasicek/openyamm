"""Assemble all engine captures after review_tour_01.yml finishes."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
import yaml

PROJECT = Path(__file__).resolve().parent
tour = yaml.safe_load((PROJECT / 'review_tour_01.yml').read_text())
folder = Path(tour['output_dir'])
shots = []
for shot in tour['shots']:
    matches = list(folder.glob('*' + shot['name'] + '.png'))
    assert len(matches) == 1, f"Missing or ambiguous engine capture: {shot['name']}"
    shots.append((shot['name'], matches[0]))
assert shots
sheet = Image.new('RGB', (1280, ((len(shots) + 1) // 2) * 390), '#161619')
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('DejaVuSans.ttf', 18)
for index, (name, path) in enumerate(shots):
    x, y = (index % 2) * 640, (index // 2) * 390
    with Image.open(path) as source:
        picture = ImageOps.contain(source.convert('RGB'), (640, 360))
        sheet.paste(picture, (x, y + 30))
    draw.text((x + 10, y + 5), name, fill='#eeeeee', font=font)
sheet.save(folder / 'sheet.jpg', quality=92)
print(folder / 'sheet.jpg')
