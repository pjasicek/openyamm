"""Review Treant at fixed native coordinates, including ordered timelines and actual 2x pixels."""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

P = Path(__file__).resolve().parent
reg = json.loads((P / 'registration.json').read_text())
manifest = json.loads((P / 'manifest.json').read_text())
window = json.loads((P / 'review/contact_settings.json').read_text())['window']
w, h = window[2] - window[0], window[3] - window[1]


def sprite(name, restored, scale=1):
    if restored:
        origin = reg[name]['canvas_origin_px']
        im = Image.open(P / f'aligned_2x/{name}.png').crop(
            [window[j] * 2 - origin[j % 2] for j in range(4)])
        if scale != 2:
            im = im.convert('RGBa').resize((w * scale, h * scale), Image.Resampling.LANCZOS).convert('RGBA')
    else:
        im = Image.open(P / f'native/{name}.png').crop(window).resize(
            (w * scale, h * scale), Image.Resampling.NEAREST)
    return im


for action in ['attack', 'hit', 'death']:
    sequence = manifest['animations'][action]['directions']['0']
    columns = min(6, len(sequence))
    row_height = h * 2 + 40
    out = Image.new('RGB', (w * columns, row_height * math.ceil(len(sequence) / columns)), '#292929')
    draw = ImageDraw.Draw(out)
    for i, entry in enumerate(sequence):
        name = entry['frame']
        x, y = i % columns * w, i // columns * row_height
        draw.text((x + 3, y + 3), f'{i + 1}: {name} {entry["duration_ms"]}ms', fill='white')
        for restored in [False, True]:
            im = sprite(name, restored)
            tile = Image.new('RGB', im.size, '#eaeaea' if restored else '#292929')
            tile.paste(im, mask=im.getchannel('A'))
            out.paste(tile, (x, y + 22 + int(restored) * (h + 8)))
    out.save(P / f'review/sequence_{action}.png')

names = ['m479ab0', 'm479ai0', 'm479na0', 'm479df0']
out = Image.new('RGB', (w * 4, h * 4 + 52), '#eaeaea')
draw = ImageDraw.Draw(out)
for i, name in enumerate(names):
    im = sprite(name, True, 2)
    x, y = i % 2 * w * 2, i // 2 * (h * 2 + 26)
    draw.text((x + 3, y + 3), name + ' actual 2x pixels', fill='black')
    out.paste(im, (x, y + 26), im)
out.save(P / 'review/crispness_runtime.png')

# One native palette means every enhanced mask must be zero, for every frame.
assert all(Image.open(P / f'masks_2x/{n}.png').getextrema() == (0, 0) for n in reg)
(P / 'review/mask_review.json').write_text(json.dumps({
    'frames': len(reg), 'palette': 530, 'all_masks_zero': True,
    'reason': 'All three native descriptors use the same original palette; no recolorable region is required.'
}, indent=2) + '\n')
