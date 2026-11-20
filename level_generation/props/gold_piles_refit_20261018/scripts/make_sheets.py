"""Contact sheets for every owned pile and every LOD."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
rows = json.loads((PROJECT / 'ownership.json').read_text())


def sheet(group, headings, paths, destination):
    size = 220
    canvas = Image.new('RGB', (size * len(headings), 50 + len(group) * size), (32, 33, 37))
    draw = ImageDraw.Draw(canvas)
    for column, title in enumerate(headings):
        draw.text((column * size + 8, 10), title, fill='white')
    for n, row in enumerate(group):
        icon = row['icon']
        for column, pattern in enumerate(paths):
            path = PROJECT / pattern.format(icon=icon)
            assert path.exists(), path
            image = Image.open(path).convert('RGBA')
            image.thumbnail((size - 12, size - 32), Image.Resampling.LANCZOS)
            canvas.paste(image, (column * size + (size-image.width)//2,
                                50+n*size+25+(size-32-image.height)//2), image)
        draw.text((8, 50+n*size+5), icon, fill='white')
    canvas.save(PROJECT / destination, quality=94)


paths = ['references/icons/{icon}.png', 'review/baseline/{icon}_three_quarter.png',
         'review/clay/{icon}_three_quarter.png', 'review/replacement/{icon}_three_quarter.png',
         'review/replacement/{icon}_low.png', 'review/replacement/{icon}_above.png',
         'review/replacement/{icon}_underside.png']
for page in range(2):
    sheet(rows[page*5:(page+1)*5], ['ICON', 'BASELINE', 'CLAY', '3/4', 'LOW', 'ABOVE', 'UNDERSIDE'],
          paths, f'review/comparison_{page+1}.jpg')
sheet(rows, ['LOD0', 'LOD1', 'LOD2', 'LOD3'],
      [f'review/{mode}/{{icon}}_three_quarter.png' for mode in ['replacement', 'lod1', 'lod2', 'lod3']],
      'review/lod_comparison.jpg')
