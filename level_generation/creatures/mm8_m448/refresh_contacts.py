"""Refresh selected-art contacts after deterministic mask-only corrections."""
import json
import numpy as np
from PIL import Image, ImageDraw
from process import ROOT, queue
from review_evidence import bg


def run():
    jobs = json.loads((ROOT / 'compact_jobs.json').read_text())['jobs']
    for key, job in jobs.items():
        sheet = Image.new('RGB', (256 * len(job['frames']), 1400), (35, 35, 35))
        draw = ImageDraw.Draw(sheet)
        for col, name in enumerate(job['frames']):
            native = Image.new('RGBA', (576, 576))
            native.paste(queue.native(ROOT, name).resize((512, 512), Image.Resampling.NEAREST), (32, 32))
            base = np.array(Image.open(ROOT / 'toned_2x' / (name + '.png')))
            mask = np.array(Image.open(ROOT / 'masks_2x' / (name + '.png'))) / 255
            base[:, :, :3] = np.round(base[:, :, :3] * (1 - .65 * mask[:, :, None]) +
                np.array([255, 70, 30]) * .65 * mask[:, :, None]).astype(np.uint8)
            pictures = [native] + [Image.open(ROOT / 'previews' / f'{name}_{p}.png') for p in [449, 450, 451]]
            pictures.append(Image.fromarray(base))
            for row, im in enumerate(pictures):
                thumb = im.convert('RGBa').resize((256, 256), Image.Resampling.LANCZOS).convert('RGBA')
                sheet.paste(bg(thumb, (35, 35, 35)), (col * 256, row * 280 + 24))
                draw.text((col * 256 + 3, row * 280 + 4), name + ' ' + str(['native', 449, 450, 451, 'mask'][row]), fill='white')
        sheet.save(ROOT / 'review' / (key + '_combined.png'))


if __name__ == '__main__':
    run()
