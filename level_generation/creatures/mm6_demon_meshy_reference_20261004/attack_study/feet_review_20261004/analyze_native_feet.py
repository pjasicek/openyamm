"""Inspect native attack feet in one unchanged coordinate system."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path('/home/pjasicek/github/OpenYAMM')
STAGE = Path(__file__).resolve().parent
SOURCE = ROOT / 'level_generation/creatures/mm6_dmn'
NAMES = ['dmnatk' + letter + '0' for letter in 'abcdef']
IMAGES = [Image.open(SOURCE / 'native' / (name + '.png')).convert('RGBA') for name in NAMES]
MASKS = [np.asarray(image)[:, :, 3] > 0 for image in IMAGES]
BACKGROUND = (34, 38, 43)
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
SMALL_FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)


def plate(filename, box, scale, columns, overlays=False):
    width, height = (box[2] - box[0]) * scale, (box[3] - box[1]) * scale
    cell_width, cell_height = width + 20, height + 62
    sheet = Image.new('RGB', (columns * cell_width, ((len(NAMES) + columns - 1) // columns) * cell_height), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    for index, (name, original) in enumerate(zip(NAMES, IMAGES)):
        x = (index % columns) * cell_width + 10
        y = (index // columns) * cell_height
        draw.text((x, y + 6), f'{name} | {index * 125}-{(index + 1) * 125} ms', font=FONT, fill=(235, 238, 241))
        draw.text((x, y + 31), 'A reference: cyan | current: orange' if overlays else f'Native crop {box}; {scale}x nearest',
                  font=SMALL_FONT, fill=(175, 185, 195))
        if overlays:
            a, b = MASKS[0], MASKS[index]
            rgb = np.zeros((*a.shape, 4), dtype=np.uint8)
            rgb[a & b] = (160, 165, 173, 255)
            rgb[a & ~b] = (35, 220, 240, 255)
            rgb[b & ~a] = (255, 135, 45, 255)
            crop = Image.fromarray(rgb).crop(box)
        else:
            crop = original.crop(box)
        crop = crop.resize((width, height), Image.Resampling.NEAREST)
        sheet.paste(crop, (x, y + 58), crop)
    sheet.save(STAGE / filename)


plate('native_legs_aligned.png', (105, 175, 240, 334), 4, 3)
plate('native_feet_aligned.png', (110, 270, 235, 334), 6, 3)
plate('native_feet_silhouette_comparison.png', (110, 270, 235, 334), 6, 3, overlays=True)

# Common crop, with transparent pixels composited. APNG preserves exact holds;
# GIF's centisecond limit requires alternating 120/130 ms holds.
gif_frames = []
for index, original in enumerate(IMAGES):
    frame = Image.new('RGB', (600, 668), BACKGROUND)
    draw = ImageDraw.Draw(frame)
    draw.text((20, 10), f'Native MM6 demon attack: {NAMES[index]} ({index * 125} ms)', font=FONT, fill=(235, 238, 241))
    crop = original.crop((105, 175, 240, 334)).resize((540, 636), Image.Resampling.NEAREST)
    frame.paste(crop, (30, 32), crop)
    gif_frames.append(frame)
gif_frames[0].save(STAGE / 'native_legs_playback.gif', save_all=True, append_images=gif_frames[1:],
                   duration=[120, 130, 120, 130, 120, 130], loop=0, disposal=2)
gif_frames[0].save(STAGE / 'native_legs_playback.png', save_all=True, append_images=gif_frames[1:],
                   duration=125, loop=0)

for region, box in [('right', (110, 278, 175, 334)), ('left', (180, 278, 236, 334))]:
    scale = 10
    width, height = (box[2] - box[0]) * scale, (box[3] - box[1]) * scale
    sheet = Image.new('RGB', ((width + 12) * 3, (height + 42) * 2), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    for index, original in enumerate(IMAGES):
        x, y = index % 3 * (width + 12), index // 3 * (height + 42)
        crop = original.crop(box).resize((width, height), Image.Resampling.NEAREST)
        sheet.paste(crop, (x, y + 34), crop)
        draw.text((x + 4, y + 4), f'{NAMES[index]} anatomical {region}; native coordinate grid',
                  font=SMALL_FONT, fill='white')
        for row in range(280, 331, 10):
            line_y = y + 34 + (row - box[1]) * scale
            draw.line((x, line_y, x + width, line_y), fill=(80, 85, 90))
            draw.text((x + 2, line_y + 2), str(row), font=SMALL_FONT, fill=(170, 170, 170))
        for column in range(((box[0] + 9) // 10) * 10, box[2], 10):
            line_x = x + (column - box[0]) * scale
            draw.line((line_x, y + 34, line_x, y + 34 + height), fill=(65, 70, 75))
            draw.text((line_x + 2, y + 34), str(column), font=SMALL_FONT, fill=(170, 170, 170))
    sheet.save(STAGE / f'native_{region}_foot_grid.png')


def region_metrics(mask, reference, box):
    x0, y0, x1, y1 = box
    area = mask[y0:y1, x0:x1]
    baseline = reference[y0:y1, x0:x1]
    rows, columns = np.nonzero(area)
    bottom = np.flatnonzero(area[-1])
    union = (area | baseline).sum()
    return {
        'roi_xyxy': list(box),
        'alpha_bbox_xyxy': [int(columns.min() + x0), int(rows.min() + y0),
                            int(columns.max() + x0 + 1), int(rows.max() + y0 + 1)],
        'bottom_row_y': y1 - 1,
        'bottom_row_occupied_x': (bottom + x0).tolist(),
        'silhouette_iou_with_A': float((area & baseline).sum() / union),
        'alpha_changed_pixels_vs_A': int((area != baseline).sum()),
    }


sources = json.loads((SOURCE / 'sources.json').read_text())
records = []
for name, image, mask in zip(NAMES, IMAGES, MASKS):
    path = SOURCE / 'native' / (name + '.png')
    source = sources['sources'][name]
    # The old mounted path in sources.json has since been retired. These preserved
    # reference BMPs have the identical recorded hashes and embedded native palette.
    bmp_path = ROOT / 'reference/mmerge_data_forus/Data/mmmerge.sprites.lod' / (name + '.bmp')
    bmp = Image.open(bmp_path)
    x0, y0, x1, y1 = source['native_offset']
    extracted = np.asarray(image)[y0:y1, x0:x1]
    source_sha = hashlib.sha256(bmp_path.read_bytes()).hexdigest()
    rgb_exact = bool(np.array_equal(extracted[:, :, :3], np.asarray(bmp.convert('RGB'))))
    alpha_exact = bool(np.array_equal(extracted[:, :, 3] > 0, np.asarray(bmp) != 0))
    assert source_sha == source['sha256'] and rgb_exact and alpha_exact, name
    records.append({
        'name': name,
        'native_png_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'original_bmp': source['path'],
        'original_bmp_sha256': source['sha256'],
        'verified_preserved_bmp': str(bmp_path.relative_to(ROOT)),
        'original_bmp_hash_matches': source_sha == source['sha256'],
        'original_colour_and_alpha_exact': rgb_exact and alpha_exact,
        'native_offset_xyxy': source['native_offset'],
        'canvas_wh': list(image.size),
        'anatomical_right_foot_screen_left': region_metrics(mask, MASKS[0], (110, 310, 174, 330)),
        'anatomical_left_foot_screen_right': region_metrics(mask, MASKS[0], (181, 310, 235, 330)),
    })
(STAGE / 'pixel_measurements.json').write_text(json.dumps({
    'source': 'Untouched native colour/alpha PNG extraction, not restored sprites or the generated 3D model',
    'coordinate_system': '354x330 logical canvas; x right, y down; anatomical right is screen left',
    'logical_pivot': sources['logical_pivot'],
    'native_hold_ms': 125,
    'native_total_ms': 750,
    'playback_timing': {'apng_holds_ms': [125] * 6, 'gif_holds_ms': [120, 130, 120, 130, 120, 130],
                        'total_ms': 750},
    'interpretation_limit': 'Bottom row 329 is the source image boundary, not an independently visible floor. '
                            'Foot ROIs avoid most of the central tail; their alpha changes measure projected shape, '
                            'not bone angles or unique 3D motion.',
    'frames': records,
}, indent=2) + '\n')
print('Saved aligned leg/foot plates, silhouette comparison, playback and pixel measurements')
