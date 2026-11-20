"""Compare archived overlap masters with the selected continuation at native placement."""
import json
from PIL import Image, ImageDraw
from process import ROOT, queue


def run():
    records = sorted((ROOT / 'checkpoints/overlaps').glob('*/*/registration.json'))
    sheet = Image.new('RGB', (1152, len(records) * 408), (35, 35, 35))
    draw = ImageDraw.Draw(sheet)
    for row, path in enumerate(records):
        name = path.parent.name
        native = Image.new('RGBA', (576, 576))
        native.paste(queue.native(ROOT, name).resize((512, 512), Image.Resampling.NEAREST), (32, 32))
        old = Image.open(path.parent / 'toned_2x.png').convert('RGBA')
        selected = Image.open(ROOT / 'toned_2x' / (name + '.png')).convert('RGBA')
        boxes = [im.getchannel('A').point(lambda a: 255 if a >= 16 else 0).getbbox()
                 for im in [native, old, selected]]
        box = (max(0, min(b[0] for b in boxes) - 12), max(0, min(b[1] for b in boxes) - 12),
               min(576, max(b[2] for b in boxes) + 12), min(576, max(b[3] for b in boxes) + 12))
        for col, (label, im) in enumerate([('native', native), ('previous', old), ('selected', selected)]):
            pic = im.crop(box)
            pic.thumbnail((380, 380), Image.Resampling.LANCZOS)
            bg = Image.new('RGBA', pic.size, (35, 35, 35, 255))
            bg.alpha_composite(pic)
            sheet.paste(bg.convert('RGB'), (col * 384, row * 408 + 24))
            draw.text((col * 384 + 3, row * 408 + 3), name + ' ' + label, fill='white')
    sheet.save(ROOT / 'review/overlap_selection.png')
    print(len(records), 'overlap comparisons')


if __name__ == '__main__':
    run()
