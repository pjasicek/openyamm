"""Make aligned inspection plates from untouched native sprite pixels."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

root = Path('/home/pjasicek/github/OpenYAMM')
stage = Path(__file__).resolve().parent
source = root / 'level_generation/creatures/mm6_dmn'
stage.mkdir(exist_ok=True)
names = ['dmnatk' + letter + '0' for letter in 'abcdef']
canvas = (354, 334)
scale = 2
cell = (canvas[0] * scale, canvas[1] * scale + 32)
sheet = Image.new('RGB', (cell[0] * 3, cell[1] * 2), (34, 38, 43))
draw = ImageDraw.Draw(sheet)
records = []
for index, name in enumerate(names):
    path = source / 'native' / (name + '.png')
    image = Image.open(path).convert('RGBA')
    mask = np.array(image)[:, :, 3] > 0
    x, y = (index % 3) * cell[0], (index // 3) * cell[1]
    layer = Image.new('RGBA', canvas)
    layer.alpha_composite(image)
    layer = layer.resize((canvas[0] * scale, canvas[1] * scale), Image.Resampling.NEAREST)
    sheet.paste(layer, (x, y + 32), layer)
    draw.text((x + 12, y + 10), f'{name}  |  {index * 125}-{(index + 1) * 125} ms', fill=(235, 238, 241))
    draw.line((x, y + 32 + 329 * scale, x + cell[0], y + 32 + 329 * scale), fill=(100, 116, 130))
    records.append({'frame': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'size': list(image.size), 'opaque_pixels': int(mask.sum()),
                    'alpha_bbox': list(image.getbbox()), 'hold_ms': 125,
                    'source_path': str(path.relative_to(root))})
sheet.save(stage / 'native_attack_aligned_2x.png')
detail = Image.new('RGB', (6 * 420, 330 * 2), (34, 38, 43))
draw = ImageDraw.Draw(detail)
for index, name in enumerate(names):
    image = Image.open(source / 'native' / (name + '.png')).convert('RGBA')
    for row, box in enumerate([(75, 65, 260, 165), (0, 80, 354, 280)]):
        crop = image.crop(box)
        factor = min(400 / crop.width, 295 / crop.height)
        crop = crop.resize((round(crop.width * factor), round(crop.height * factor)), Image.Resampling.NEAREST)
        detail.paste(crop, (index * 420 + (420 - crop.width) // 2, row * 330 + 28), crop)
        draw.text((index * 420 + 8, row * 330 + 8), name + (' head/shoulders' if row == 0 else 'arms/hands'),
                  fill=(235, 238, 241))
detail.save(stage / 'native_attack_details.png')
# Genuine stored standing views, all at the same native coordinate origin.
views = Image.new('RGB', (5 * 400, 730), (34, 38, 43))
draw = ImageDraw.Draw(views)
for view in range(5):
    name = 'dmnstda' + str(view)
    image = Image.open(source / 'native' / (name + '.png')).convert('RGBA')
    layer = Image.new('RGBA', canvas)
    layer.alpha_composite(image)
    layer = layer.resize((400, 377), Image.Resampling.NEAREST)
    views.paste(layer, (view * 400, 32), layer)
    draw.text((view * 400 + 8, 10), name + ' genuine stored anatomy view', fill=(235, 238, 241))
views.crop((0, 0, views.width, 420)).save(stage / 'native_standing_views.png')
(stage / 'native_reference_audit.json').write_text(json.dumps({
    'attack_frames': records, 'native_animation_duration_ms': 750,
    'native_attack_views': 1, 'runtime_other_views_reuse_Image1': True,
    'attack2_aliases_attack': True, 'image_scaling_for_inspection_only': 'nearest neighbour',
    'no_generated_restoration_used_for_pose_evidence': True,
}, indent=2) + '\n')
print('Prepared six aligned native attack poses and the stored standing anatomy views')
