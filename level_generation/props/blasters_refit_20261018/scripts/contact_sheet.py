"""Compare each weapon with its authoritative icon and previous component model."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

P = Path(__file__).resolve().parents[1]


def main():
    rows = json.loads((P / 'ownership.json').read_text())
    assert len(rows) == 5
    sheet = Image.new('RGB', (2240, 1660), (38, 41, 45))
    draw = ImageDraw.Draw(sheet)
    for col, title in enumerate(['Icon', 'Previous model', 'New clay', 'New above', 'New three-quarter', 'New low', 'New underside']):
        draw.text((col*320+6, 8), title, fill='white')
    for row, entry in enumerate(rows):
        icon = entry['icon']
        paths = [P/'references/icons'/f'{icon}.png', P/'review/baseline'/f'{icon}_threequarter.png',
                 P/'review/meshy_clay'/f'{icon}_three_quarter.png']
        paths += [P/'review/meshy'/f'{icon}_{view}.png' for view in ['above', 'three_quarter', 'low', 'underside']]
        for col, path in enumerate(paths):
            assert path.exists(), path
            image = Image.open(path).convert('RGBA')
            if col == 3:
                image = image.transpose(Image.Transpose.ROTATE_270)
            scale = min(300/image.width, 290/image.height)
            image = image.resize((round(image.width*scale), round(image.height*scale)), Image.Resampling.LANCZOS)
            sheet.paste(image, (col*320+(320-image.width)//2, 35+row*325+(290-image.height)//2), image)
        draw.text((6, 35+row*325+293), icon+' '+entry['items'][0]['name'], fill='white')
    sheet.save(P / 'review/comparison.png')


if __name__ == '__main__':
    main()
