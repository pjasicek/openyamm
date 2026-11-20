"""Preserve native fringe forms where two-material decomposition cannot represent them."""
import json
from PIL import ImageDraw
from scipy.ndimage import gaussian_filter, binary_dilation
from common import *

F = P / 'transitions/grey_fringe_v3'
F.mkdir(parents=True, exist_ok=True)
bg = read(P / 'references/gdtyl.png')
fg = read(P / 'references/gstyl.png')
new_bg = read(M / 'materials/grey_dirt.png')
new_fg = read(M / 'materials/grey_stone.png')
yy, xx = np.mgrid[:512, :512]; border = np.minimum.reduce([xx, yy, 511 - xx, 511 - yy])
sheet = Image.new('RGB', (1024, 1120), '#202933'); draw = ImageDraw.Draw(sheet)
for row, name in enumerate(('gse', 'gsn', 'gsne', 'gsnw')):
    original = read(P / 'references' / (name + '.png'))
    mismatch = (np.max(abs(original - bg), 2) > 3) & (np.max(abs(original - fg), 2) > 3)
    mismatch = binary_dilation(mismatch, iterations=2)
    weight = np.asarray(Image.fromarray(mismatch.astype('float32')).resize((512, 512), Image.Resampling.BICUBIC))
    weight = np.clip(gaussian_filter(weight, 4), 0, 1) * np.clip((border - 8) / 32, 0, 1)
    native = read(P / 'references' / (name + '.png'), 512)
    fields = np.load(P / 'transitions/fields' / (name + '.npz')); a = fields['coverage'][:, :, None]
    mix = seams.srgb(seams.linear(new_bg) * (1 - a) + seams.linear(new_fg) * a).astype(float)
    detail = mix - gaussian_filter(mix, (3, 3, 0))
    # The native source defines local form and value. Master detail supplies small
    # restored grain, bounded so a master crack cannot cut through a fringe stone.
    detail = np.clip(detail, -6, 6)
    restored = np.clip(native + detail, 0, 255)
    previous = read(OUT / (name + '.png'), 512)
    pixels = previous * (1 - weight[:, :, None]) + restored * weight[:, :, None]
    save(F / (name + '.png'), seams.reduce(seams.pad(pixels, 'edge')))
    save(F / (name + '_weight.png'), weight * 255)
    for col, path in enumerate((P / 'references' / (name + '.png'), OUT / (name + '.png'), F / (name + '.png'), F / (name + '_weight.png'))):
        sheet.paste(Image.open(path).convert('RGB').resize((256, 256)), (col * 256, row * 280 + 24))
        draw.text((col * 256 + 3, row * 280 + 5), name + ' ' + ['native','scalar shade','local native form','insertion'][col],fill='white')
sheet.save(F / 'comparison.png')
(F / 'pilot.json').write_text(json.dumps(dict(status='visual_pilot_only_no_runtime_changes', method='Native edge forms plus bounded restored material grain'),indent=2)+'\n')
