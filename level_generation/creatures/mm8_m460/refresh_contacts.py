"""Refresh selected-art contacts after deterministic mask-only corrections."""
import json
import numpy as np
from PIL import Image, ImageDraw
from process import ROOT, queue
def bg(im,color):
    out=Image.new('RGBA',im.size,(*color,255));out.alpha_composite(im);return out.convert('RGB')


def run():
    jobs = json.loads((ROOT / 'compact_jobs.json').read_text())['jobs']
    for key, job in jobs.items():
        if any(not (ROOT/'toned_2x'/f'{n}.png').exists() for n in job['frames']):continue
        sheet = Image.new('RGB', (256 * len(job['frames']), 1400), (35, 35, 35))
        draw = ImageDraw.Draw(sheet)
        for col, name in enumerate(job['frames']):
            native = Image.new('RGBA', (576, 576))
            native.paste(queue.native(ROOT, name).resize((512, 512), Image.Resampling.NEAREST), (32, 32))
            base = np.array(Image.open(ROOT / 'toned_2x' / (name + '.png')))
            mask = np.array(Image.open(ROOT / 'masks_2x' / (name + '.png'))).max(axis=2) / 255
            base[:, :, :3] = np.round(base[:, :, :3] * (1 - .65 * mask[:, :, None]) +
                np.array([255, 70, 30]) * .65 * mask[:, :, None]).astype(np.uint8)
            pictures = [native] + [Image.open(ROOT / 'previews' / f'{name}_{p}.png') for p in [461, 462, 463]]
            pictures.append(Image.fromarray(base))
            for row, im in enumerate(pictures):
                thumb = im.convert('RGBa').resize((256, 256), Image.Resampling.LANCZOS).convert('RGBA')
                sheet.paste(bg(thumb, (35, 35, 35)), (col * 256, row * 280 + 24))
                draw.text((col * 256 + 3, row * 280 + 4), name + ' ' + str(['native', 461, 462, 463, 'mask'][row]), fill='white')
        sheet.save(ROOT / 'review' / (key + '_combined.png'))


if __name__ == '__main__':
    run()
