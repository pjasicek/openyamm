"""Compare archived overlap masters with the selected continuation at native placement."""
import json
from PIL import Image, ImageDraw
from process import ROOT, queue


def run():
    records = sorted((ROOT / 'checkpoints/overlaps').glob('*/*/registration.json'))
    pages = []
    for index, path in enumerate(records):
        row = index % 6
        if row == 0:
            sheet = Image.new('RGB', (768, min(6, len(records) - index) * 272), (35, 35, 35))
            draw = ImageDraw.Draw(sheet); pages.append(sheet)
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
            pic.thumbnail((252, 244), Image.Resampling.LANCZOS)
            bg = Image.new('RGBA', pic.size, (35, 35, 35, 255))
            bg.alpha_composite(pic)
            sheet.paste(bg.convert('RGB'), (col * 256, row * 272 + 24))
            draw.text((col * 256 + 3, row * 272 + 3), name + ' ' + label, fill='white')
    for index, sheet in enumerate(pages):
        sheet.save(ROOT / f'review/overlap_selection_{index}.png')
    print(len(records), 'overlap comparisons')


if __name__ == '__main__':
    run()
