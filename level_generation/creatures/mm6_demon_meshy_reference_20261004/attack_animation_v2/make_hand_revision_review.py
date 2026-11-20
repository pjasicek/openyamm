"""Full-resolution forearm/hand plates and an honest rejected-v1 versus v2 comparison."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

stage = Path(__file__).resolve().parent
plates = stage / 'review_plates'
plates.mkdir(exist_ok=True)
source = np.load(stage / 'source_geometry.npz')
current = np.load(stage / 'attack_pose_arrays.npz')['vertices']
previous = np.load(stage.parent / 'attack_animation/attack_pose_arrays.npz')['vertices']
names = list(source['group_names'])
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
selectors = {}
for side in ('Right', 'Left'):
    columns = [i for i, name in enumerate(names)
               if name == 'mixamorig:' + side + 'ForeArm' or name.startswith('mixamorig:' + side + 'Hand')]
    selectors[side] = source['weights'][:, columns].sum(1) > .55

def crop(frame, side, version='current', view='front'):
    directory, poses = (stage, current) if version == 'current' else (stage.parent / 'attack_animation', previous)
    v = poses[frame, selectors[side]]
    horizontal = v[:, 0] if view == 'front' else v[:, 1] + .10
    xy = np.stack([650 + horizontal * 1300 / 2.35, 550 + (.86 - v[:, 2]) * 1300 / 2.35], axis=1)
    lo, hi = np.floor(xy.min(0) - 18).astype(int), np.ceil(xy.max(0) + 18).astype(int)
    bounds = (max(0, int(lo[0])), max(0, int(lo[1])), min(1300, int(hi[0])), min(1100, int(hi[1])))
    return Image.open(directory / 'review_frames' / f'{view}_{frame:02d}.png').convert('RGB').crop(bounds)

for side in ('Right', 'Left'):
    for view in ('front', 'side'):
        for first in range(0, 37, 6):
            board = Image.new('RGB', (1500, 1040), (24, 30, 36))
            draw = ImageDraw.Draw(board)
            for offset, frame in enumerate(range(first, min(first + 6, 37))):
                detail = crop(frame, side, view=view)
                assert detail.width <= 500 and detail.height <= 480, (side, view, frame, detail.size)
                x, y = offset % 3 * 500, offset // 3 * 520
                board.paste(detail, (x + (500 - detail.width) // 2, y + 35))
                draw.text((x + 8, y + 8), f'{side} #{frame:02d} {view} - original render pixels', font=font, fill='white')
            board.save(plates / f'forearm_{side.lower()}_{view}_{first:02d}.png')

targets = [('Right', 19), ('Right', 21), ('Right', 23), ('Right', 28), ('Left', 0), ('Left', 21)]
comparison = Image.new('RGB', (1800, 1520), (24, 30, 36))
draw = ImageDraw.Draw(comparison)
for offset, (side, frame) in enumerate(targets):
    x, y = offset % 2 * 900, offset // 2 * 500
    draw.text((x + 10, y + 8), f'{side} frame {frame}: rejected v1 | corrected v2', font=font, fill='white')
    for version, left in [('previous', 0), ('current', 450)]:
        detail = crop(frame, side, version)
        assert detail.width <= 450 and detail.height <= 450, (side, frame, version, detail.size)
        comparison.paste(detail, (x + left + (450 - detail.width) // 2, y + 40))
comparison.save(stage / 'hand_revision_comparison.png')

# Additional anchor/full-export boards do not replace the original-pixel detail plates.
for view in ('rear', 'opposite', 'threequarter', 'walking', 'running'):
    paths = sorted((stage / 'review_frames').glob(view + '_*.png'))
    board = Image.new('RGB', (1800, 1140), (24, 30, 36))
    for i, path in enumerate(paths):
        x, y = i % 4 * 450, i // 4 * 570
        picture = Image.open(path).convert('RGB')
        picture.thumbnail((450, 540), Image.Resampling.LANCZOS)
        board.paste(picture, (x + (450 - picture.width) // 2, y + 28))
        ImageDraw.Draw(board).text((x + 6, y + 5), path.stem, font=font, fill='white')
    board.save(plates / f'{view}_anchors.jpg', quality=95)

for view in ('front', 'side', 'threequarter', 'opposite_threequarter'):
    paths = sorted((stage / 'export_review_frames').glob(view + '_*.png'))
    if not paths:
        continue
    board = Image.new('RGB', (1800, 1140), (24, 30, 36))
    for i, path in enumerate(paths):
        x, y = i % 4 * 450, i // 4 * 570
        picture = Image.open(path).convert('RGB')
        picture.thumbnail((450, 540), Image.Resampling.LANCZOS)
        board.paste(picture, (x + (450 - picture.width) // 2, y + 28))
        ImageDraw.Draw(board).text((x + 6, y + 5), path.stem, font=font, fill='white')
    board.save(plates / f'export_{view}.jpg', quality=95)
print('Built full-resolution forearm/hand plates and rejected-v1 / corrected-v2 comparison.')
