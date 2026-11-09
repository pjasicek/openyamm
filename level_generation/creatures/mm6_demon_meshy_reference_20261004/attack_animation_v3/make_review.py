"""Compose unscaled diagnostic crops and playback previews from review renders."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

STAGE = Path(__file__).resolve().parent
FRAMES = STAGE / 'review_frames'
PLATES = STAGE / 'review_plates'
PLATES.mkdir(exist_ok=True)
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
SMALL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
BG = (24, 30, 36)
FRONT_LEGS = (360, 550, 935, 1058)
SIDE_LEGS = (560, 550, 930, 1058)
FRONT_FEET = (360, 820, 935, 1058)
SIDE_FEET = (560, 820, 930, 1058)


def crop(view, frame, box):
    return Image.open(FRAMES / f'{view}_{frame:02d}.png').convert('RGB').crop(box)


for start in range(0, 37, 6):
    indices = range(start, min(start + 6, 37))
    for kind, first, second in [('legs', FRONT_LEGS, SIDE_LEGS), ('feet', FRONT_FEET, SIDE_FEET)]:
        height = first[3] - first[1]
        sheet = Image.new('RGB', (1930, (height + 44) * 3), BG)
        draw = ImageDraw.Draw(sheet)
        for offset, frame in enumerate(indices):
            x, y = offset % 2 * 965, offset // 2 * (height + 44)
            draw.text((x + 8, y + 6), f'#{frame:02d} | {frame / 48 * 1000:.1f} ms | front / right profile | 100% pixels',
                      font=SMALL, fill='white')
            sheet.paste(crop('front', frame, first), (x + 5, y + 36))
            sheet.paste(crop('side', frame, second), (x + 590, y + 36))
            for box, horizontal in [(first, x + 5), (second, x + 590)]:
                # Known floor height in the common orthographic cameras.
                ground = 550 + .86 * 1300 / 2.35
                line_y = y + 36 + round(ground - box[1])
                draw.line((horizontal, line_y, horizontal + box[2] - box[0], line_y), fill=(90, 115, 130))
        sheet.save(PLATES / f'{kind}_{start:02d}.png')
    full = Image.new('RGB', (1950, 1160), BG)
    draw = ImageDraw.Draw(full)
    for offset, frame in enumerate(indices):
        x, y = offset % 3 * 650, offset // 3 * 580
        image = Image.open(FRAMES / f'front_{frame:02d}.png').convert('RGB').resize((650, 550), Image.Resampling.LANCZOS)
        full.paste(image, (x, y + 30))
        draw.text((x + 8, y + 6), f'#{frame:02d} | {frame / 48 * 1000:.1f} ms', font=FONT, fill='white')
    full.save(PLATES / f'full_{start:02d}.jpg', quality=95)

# A single fixed native crop and model crop expose the foot orientation changes.
comparison = Image.new('RGB', (1680, 6 * 290), BG)
draw = ImageDraw.Draw(comparison)
for index, letter in enumerate('abcdef'):
    frame, y = index * 6, index * 290
    native = Image.open(STAGE.parent.parent / 'mm6_dmn/native' / f'dmnatk{letter}0.png').convert('RGBA')
    native = native.crop((110, 270, 235, 334)).resize((500, 256), Image.Resampling.NEAREST)
    comparison.paste(native, (0, y + 30), native)
    comparison.paste(crop('before_front', frame, FRONT_FEET), (515, y + 42))
    comparison.paste(crop('front', frame, FRONT_FEET), (1100, y + 42))
    for x, label in [(8, 'native'), (523, 'previous'), (1108, 'revised')]:
        draw.text((x, y + 6), f'{letter.upper()} / #{frame:02d} / {index * 125} ms | {label}', font=FONT, fill='white')
comparison.save(STAGE / 'foot_revision_comparison.png')

# All close-up camera pixels remain available; compose paired anchors for review.
for frame in [0, 6, 12, 18, 24, 30]:
    sheet = Image.new('RGB', (1300, 2 * 590), BG)
    draw = ImageDraw.Draw(sheet)
    for row, view in enumerate(['before_feet_detail', 'feet_detail']):
        image = Image.open(FRAMES / f'{view}_{frame:02d}.png').convert('RGB')
        # A common cut of the close-up render, not a pose-dependent fitting.
        image = image.crop((0, 475, 1300, 1035))
        sheet.paste(image, (0, row * 590 + 30))
        draw.text((10, row * 590 + 6), f'#{frame:02d} | {"previous" if row == 0 else "revised"} | original close-up pixels',
                  font=FONT, fill='white')
    sheet.save(PLATES / f'foot_detail_{frame:02d}.png')

full_animation, feet_animation = [], []
for frame in range(37):
    image = Image.new('RGB', (1300, 585), BG)
    image.paste(Image.open(FRAMES / f'front_{frame:02d}.png').convert('RGB').resize((650, 550), Image.Resampling.LANCZOS), (0, 35))
    image.paste(Image.open(FRAMES / f'side_{frame:02d}.png').convert('RGB').resize((650, 550), Image.Resampling.LANCZOS), (650, 35))
    ImageDraw.Draw(image).text((12, 8), 'MM6 demon attack | subtle foot pivot / retained body dip | 750 ms + preview pause', font=FONT, fill='white')
    full_animation.append(image)
    image = Image.new('RGB', (965, 278), BG)
    image.paste(crop('front', frame, FRONT_FEET), (0, 35))
    image.paste(crop('side', frame, SIDE_FEET), (590, 35))
    ImageDraw.Draw(image).text((8, 8), f'Attack #{frame:02d} | feet, front / right profile', font=FONT, fill='white')
    feet_animation.append(image)
durations = [max(10, (round((i + 1) / 48 * 100) - round(i / 48 * 100)) * 10) for i in range(36)] + [350]
assert sum(durations[:-1]) == 750
for name, images in [('attack_preview', full_animation), ('feet_preview', feet_animation)]:
    images[0].save(STAGE / f'{name}.gif', save_all=True, append_images=images[1:], duration=durations, loop=0, disposal=2)
print('Saved all-pose full/leg/foot plates, six 100% before/after close-ups and playback previews.')
