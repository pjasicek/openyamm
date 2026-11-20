"""Icon, clay and textured review for every owned export; no asset mutations."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
VIEWS = [('clay', 'top'), ('clay', 'low'), ('textured', 'top'),
         ('textured', 'threequarter'), ('textured', 'low'), ('textured', 'underside')]


def main():
    rows = json.loads((HERE / 'ownership.json').read_text())
    completed = [r for r in rows if (HERE / f"review/textured/{r['icon']}_underside.png").exists()]
    assert completed
    for page in range((len(completed) + 7) // 8):
        part = completed[page * 8:(page + 1) * 8]
        out = Image.new('RGB', (1720, len(part) * 260), (38, 39, 44))
        draw = ImageDraw.Draw(out)
        for row, entry in enumerate(part):
            icon = entry['icon']
            image = Image.open(ROOT / entry['icon_reference']).convert('RGBA')
            image.thumbnail((145, 218))
            out.paste(image, ((160 - image.width) // 2, row * 260 + 30), image)
            draw.text((4, row * 260 + 4), icon, fill='white')
            draw.text((4, row * 260 + 18), entry['items'][0]['name'][:24], fill='white')
            for col, (kind, view) in enumerate(VIEWS):
                f = HERE / f'review/{kind}/{icon}_{view}.png'
                image = Image.open(f)
                image.thumbnail((255, 234))
                out.paste(image, (160 + col * 260, row * 260 + 24))
                draw.text((165 + col * 260, row * 260 + 4), f'{kind}: {view}', fill='white')
        out.save(HERE / f'review/contact_{page + 1:02}.png')
    print(f'{len(completed)} icons in {(len(completed) + 7) // 8} sheets')


if __name__ == '__main__':
    main()
