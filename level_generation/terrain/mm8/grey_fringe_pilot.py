"""Compare native linear edge appearance against scalar-only grey-stone recovery."""
import json
from PIL import ImageDraw
from scipy.ndimage import distance_transform_edt, gaussian_filter
from common import *

F = P / 'transitions/grey_fringe_v2'
F.mkdir(parents=True, exist_ok=True)
background = read(P / 'references/gdtyl.png', 512)
foreground = read(P / 'references/gstyl.png', 512)
new_background = read(M / 'materials/grey_dirt.png')
new_foreground = read(M / 'materials/grey_stone.png')
sheet = Image.new('RGB', (1024, 1120), '#202933'); draw = ImageDraw.Draw(sheet)
records = []
for row, name in enumerate(('gse', 'gsn', 'gsne', 'gsnw')):
    native = read(P / 'references' / (name + '.png'), 512)
    fields = np.load(P / 'transitions/fields' / (name + '.npz'))
    alpha = fields['coverage'][:, :, None]
    old_mix = seams.linear(background) * (1 - alpha) + seams.linear(foreground) * alpha
    delta = seams.linear(native) - old_mix
    # Do not reintroduce the native, unmatched border profiles in this pilot.
    yy, xx = np.mgrid[:512, :512]
    border = np.minimum.reduce([xx, yy, 511 - xx, 511 - yy])
    delta *= np.clip((border - 8) / 32, 0, 1)[:, :, None]
    new_mix = seams.linear(new_background) * (1 - alpha) + seams.linear(new_foreground) * alpha
    pixels = seams.srgb(new_mix + delta)
    save(F / (name + '.png'), seams.reduce(seams.pad(pixels, 'edge')))
    for col, path in enumerate((P / 'references' / (name + '.png'), OUT / (name + '.png'), F / (name + '.png'))):
        sheet.paste(Image.open(path).convert('RGB').resize((256, 256)), (col * 256, row * 280 + 24))
        draw.text((col * 256 + 3, row * 280 + 5), name + ' ' + ['native', 'scalar shade', 'linear appearance'][col], fill='white')
    preview = seams.byte(128 + delta * 500)
    sheet.paste(Image.fromarray(preview).resize((256, 256)), (768, row * 280 + 24))
    draw.text((771, row * 280 + 5), 'signed appearance delta', fill='white')
    records.append(dict(name=name, delta_min=float(delta.min()), delta_max=float(delta.max())))
sheet.save(F / 'comparison.png')
(F / 'pilot.json').write_text(json.dumps(dict(status='pilot_not_runtime', tiles=records), indent=2) + '\n')
