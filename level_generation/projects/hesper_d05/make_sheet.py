"""Assemble the D5 fix review captures; refuse an incomplete tour."""
from pathlib import Path
import yaml
from PIL import Image, ImageDraw

project = Path(__file__).resolve().parent
tour = yaml.safe_load((project / 'review_tour_02.yml').read_text())
folder = Path(tour['output_dir'])
shots = sorted(folder.glob('[0-9][0-9]-*.png'))
assert len(shots) == len(tour['shots']), f'Need the complete tour, found {len(shots)} captures'
sheet = Image.new('RGB', (1920, ((len(shots) + 3) // 4) * 294), '#181818')
draw = ImageDraw.Draw(sheet)
for index, path in enumerate(shots):
    picture = Image.open(path).convert('RGB')
    picture.thumbnail((480, 270))
    x, y = index % 4 * 480, index // 4 * 294
    sheet.paste(picture, (x, y))
    draw.text((x + 8, y + 274), path.stem, fill='white')
sheet.save(folder / 'sheet.jpg', quality=92)
