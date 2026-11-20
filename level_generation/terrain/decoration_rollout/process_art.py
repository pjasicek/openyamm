"""Extract magenta-backed generated plants, unmix edges, and export grounded runtime cells."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent


def main():
    output = HERE / 'art/processed'
    output.mkdir(parents=True, exist_ok=True)
    report = {'method': 'magenta matte; nearest opaque foreground color estimate; edge unmix; premultiplied resize',
              'background': [255, 0, 255], 'families': {}}
    review = Image.new('RGB', (1024, 3 * 216), '#24242a')
    draw = ImageDraw.Draw(review)
    for row, family in enumerate(['marsh_reed', 'tropical_low', 'dead_tuft']):
        path = HERE / 'art/raw' / (family + '_magenta.png')
        rgb = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32)
        magenta = np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1]
        core = magenta < 12
        assert core.any() and (~core).any()
        nearest = ndimage.distance_transform_edt(~core, return_distances=False, return_indices=True)
        foreground = rgb[nearest[0], nearest[1]]
        background = np.array([255, 0, 255], np.float32)
        direction = foreground - background
        alpha = np.clip(np.sum((rgb - background) * direction, axis=2) /
                        np.maximum(np.sum(direction * direction, axis=2), 1), 0, 1)
        alpha[core] = 1
        # The generator's nominal solid key varies slightly. Such strongly magenta samples
        # are background, not a translucent veil across the empty sheet.
        alpha[magenta > 170] = 0
        alpha[alpha < 0.03] = 0
        corrected = np.clip((rgb - (1 - alpha[..., None]) * background) /
                            np.maximum(alpha[..., None], 0.03), 0, 255)
        # Retain interior colors exactly. Only contaminated contour samples are unmixed.
        corrected[core] = rgb[core]
        residual = np.minimum(corrected[..., 0], corrected[..., 2]) - corrected[..., 1] > 12
        corrected[residual] = foreground[residual]
        labels, count = ndimage.label(alpha > 0)
        sizes = np.bincount(labels.ravel())
        for label in range(1, count + 1):
            if sizes[label] < 12:
                alpha[labels == label] = 0
        rgba = np.dstack((np.rint(corrected), np.rint(alpha * 255))).astype(np.uint8)
        rgba[alpha == 0, :3] = 0
        image = Image.fromarray(rgba, 'RGBA')
        image.save(output / (family + '_sheet.png'))
        width, height = image.size
        columns = (alpha > 0).sum(axis=0)
        central = np.arange(int(width * 0.4), int(width * 0.6))
        clear = central[columns[central] == 0]
        assert clear.size > 8, family + ': no safe split between variants'
        gaps = np.split(clear, np.where(np.diff(clear) > 1)[0] + 1)
        gap = max(gaps, key=len)
        split = int(gap[len(gap) // 2])
        crops = []
        bounds = []
        for left, right in [(0, split), (split, width)]:
            cell = image.crop((left, 0, right, height))
            box = cell.getchannel('A').getbbox()
            assert box and box[0] > 0 and box[2] < right - left and box[1] > 0 and box[3] < height
            crops.append(cell.crop(box))
            bounds.append([box[0] + left, box[1], box[2] + left, box[3]])
        scale = min(252 / max(c.width for c in crops), 188 / max(c.height for c in crops))
        files = []
        for index, crop in enumerate(crops):
            size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
            reduced = crop.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')
            cell = Image.new('RGBA', (256, 192))
            cell.paste(reduced, ((256 - size[0]) // 2, 190 - size[1]))
            pixels = np.array(cell)
            colors = pixels[..., :3].astype(int)
            fringe = (np.minimum(colors[..., 0], colors[..., 2]) - colors[..., 1] > 12) & (pixels[..., 3] > 0)
            safe = (pixels[..., 3] >= 128) & ~fringe
            nearest_safe = ndimage.distance_transform_edt(~safe, return_distances=False, return_indices=True)
            pixels[fringe, :3] = pixels[nearest_safe[0][fringe], nearest_safe[1][fringe], :3]
            cell = Image.fromarray(pixels)
            file = output / f'{family}_{index}.png'
            cell.save(file)
            a = np.asarray(cell)
            spill = (a[..., 0].astype(int) > a[..., 1].astype(int) + 20) & \
                    (a[..., 2].astype(int) > a[..., 1].astype(int) + 20) & (a[..., 3] > 32)
            assert not spill.any(), (family, index, 'magenta edge spill')
            assert cell.getchannel('A').getbbox()[3] == 190
            files.append({'path': str(file.relative_to(HERE)), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                          'opaque_pixels': int((a[..., 3] >= 128).sum()), 'magenta_spill_pixels': int(spill.sum())})
            for background_index, color in enumerate(['#24242a', '#d0caba']):
                panel = Image.new('RGBA', cell.size, color)
                panel.alpha_composite(cell)
                review.paste(panel.convert('RGB'), (background_index * 512 + index * 256, row * 216 + 24))
        draw.text((4, row * 216 + 6), family + ' | dark and light edge check', fill='white')
        report['families'][family] = {'raw_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                     'raw_size': [width, height], 'source_bounds': bounds,
                                     'common_resize_scale': scale, 'runtime_cells': files}
    review.save(HERE / 'art/edge_review.png')
    (HERE / 'art/processing.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Exported six 256x192 cells; grounded at row 190, magenta edge checks passed.')


if __name__ == '__main__':
    main()
