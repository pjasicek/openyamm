"""Magnified enhanced-cloth boundaries with deterministic palette previews."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from process import ROOT
from review_evidence import bg


def run():
    names = ['m444sa0', 'm444sa1', 'm444wa2', 'm444aa1', 'm444db1', 'm444xa2']
    sheet = Image.new('RGB', (6 * 224, 4 * 244), (35, 35, 35))
    draw = ImageDraw.Draw(sheet)
    for col, name in enumerate(names):
        mask = np.asarray(Image.open(ROOT / 'masks_2x' / (name + '.png')))
        labels, count = ndi.label(mask > 180)
        assert count
        sizes = np.bincount(labels.ravel()); sizes[0] = 0
        yy, xx = np.where(labels == sizes.argmax())
        cx, cy = int(xx.mean()), int(yy.mean())
        box = (cx - 48, cy - 48, cx + 48, cy + 48)
        for row, (palette, color) in enumerate([(445, (18, 18, 18)), (445, (235, 235, 235)),
                                               (446, (235, 235, 235)), (447, (18, 18, 18))]):
            im = Image.open(ROOT / 'previews' / f'{name}_{palette}.png').convert('RGBA').crop(box)
            patch = bg(im, color).resize((216, 216), Image.Resampling.NEAREST)
            sheet.paste(patch, (col * 224 + 4, row * 244 + 24))
            draw.text((col * 224 + 4, row * 244 + 4), f'{name} {palette}', fill='white')
    sheet.save(ROOT / 'review/material_edges.png')


if __name__ == '__main__':
    run()
