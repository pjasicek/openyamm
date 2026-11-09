"""Review selected overlap versions in complete native action order."""
import json
from PIL import Image, ImageDraw
from process import ROOT, queue
from review_evidence import bg


def run():
    source = json.loads((ROOT / 'sources.json').read_text())
    for action in ['a', 'w', 'd']:
        for view in range(5):
            names = sorted(n for n in source['sources'] if n[4] == action and n[-1] == str(view))
            if action == 'd':
                names += [f'm452xa{view}']
            aliases = source['pixel_aliases']
            assert names and all((ROOT / 'toned_2x' / (aliases.get(n, n) + '.png')).exists() for n in names)
            sheet = Image.new('RGB', (192 * len(names), 416), (35, 35, 35))
            draw = ImageDraw.Draw(sheet)
            for col, name in enumerate(names):
                canonical = aliases.get(name, name)
                native = Image.new('RGBA', (576, 576))
                native.paste(queue.native(ROOT, name).resize((512, 512), Image.Resampling.NEAREST), (32, 32))
                images = [native, Image.open(ROOT / 'toned_2x' / (canonical + '.png'))]
                for row, im in enumerate(images):
                    thumb = im.convert('RGBa').resize((192, 192), Image.Resampling.LANCZOS).convert('RGBA')
                    sheet.paste(bg(thumb, (35, 35, 35)), (col * 192, row * 208 + 16))
                    draw.text((col * 192 + 3, row * 208 + 2), name + [' native', ' 452'][row],
                              fill='white')
            sheet.save(ROOT / f'review/sequence_{action}_v{view}.png')
    print('15 complete selected action/view contacts saved')


if __name__ == '__main__':
    run()
