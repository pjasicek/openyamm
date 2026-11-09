"""Review localized AI stone restoration without changing staged/runtime assets."""
import json
import argparse
import cv2
from PIL import ImageDraw
from scipy.ndimage import gaussian_filter, binary_opening, binary_closing, binary_dilation
from common import *

F = P / 'transitions/grey_fringe_ai'
parser = argparse.ArgumentParser()
parser.add_argument('name', nargs='?', default='gsn', choices=('gsn','gse','gsne','gsnw'))
name = parser.parse_args().name
native = read(P / 'references' / (name + '.png'), 512)
generated = read(F / 'raw' / (name + '.png'), 512)
background = read(P / 'references/gdtyl.png', 512)
foreground = read(P / 'references/gstyl.png', 512)
new_bg = read(M / 'materials/grey_dirt.png')
new_fg = read(M / 'materials/grey_stone.png')

# Align broad native stone forms. Fine generated gravel is not a geometry cue.
def grey(a):
    return np.clip(gaussian_filter(a.mean(2), 4), 0, 255).astype('uint8')

flow = cv2.calcOpticalFlowFarneback(grey(native), grey(generated), None, .5, 4, 45, 5, 7, 1.5, 0)
flow = gaussian_filter(flow, (5, 5, 0))
yy, xx = np.mgrid[:512, :512]
aligned = cv2.remap(generated.astype('float32'), (xx + flow[:, :, 0]).astype('float32'),
                    (yy + flow[:, :, 1]).astype('float32'), cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE)
# Keep the native low-frequency tone; AI supplies definition at smaller scales.
restored = aligned + gaussian_filter(native - aligned, (12, 12, 0))
old = read(OUT / (name + '.png'), 512)
fields = np.load(P / 'transitions/fields' / (name + '.npz'))
alpha = fields['coverage']
shade = fields['shade']
mix = seams.srgb(seams.linear(new_bg) * (1-alpha[:, :, None]) +
                 seams.linear(new_fg) * alpha[:, :, None]) * shade[:, :, None]
# Darkness relative to the native soil isolates stones/shadows from AI-invented gravel.
stone = gaussian_filter((background-native).mean(2), 3) > 7
stone = binary_closing(binary_opening(stone, iterations=2), iterations=3)
stone_weight = np.clip(gaussian_filter(binary_dilation(stone, iterations=8).astype(float), 3), 0, 1)
exact_fg = np.max(abs(native - foreground), 2) < 4
exact_bg = np.max(abs(native - background), 2) < 4
local = gaussian_filter(binary_dilation(~(exact_fg | exact_bg), iterations=8).astype(float), 4)
border = np.minimum.reduce([xx, yy, 511-xx, 511-yy])
weight = stone_weight * local * np.clip((border-40)/32, 0, 1)
pixels = mix*(1-weight[:, :, None]) + restored*weight[:, :, None]
# Preserve exact existing screened runtime borders for this isolated pilot.
candidate = seams.reduce(seams.pad(pixels, 'edge')).copy()
previous = read(OUT / (name + '.png'))
candidate[:16] = previous[:16]; candidate[-16:] = previous[-16:]
candidate[:, :16] = previous[:, :16]; candidate[:, -16:] = previous[:, -16:]
save(F / 'runtime_pilot' / (name + '.png'), candidate)
save(F / 'aligned' / (name + '.png'), aligned)
save(F / 'weights' / (name + '.png'), weight*255)
sheet = Image.new('RGB', (1280, 290), '#202933')
draw = ImageDraw.Draw(sheet)
for i, (label, pixels) in enumerate((('native', native), ('current', old), ('AI raw', generated),
                                    ('local composite', candidate), ('insertion', weight*255))):
    image = Image.fromarray(seams.byte(pixels)).convert('RGB').resize((256,256))
    sheet.paste(image, (256*i, 28)); draw.text((256*i+4, 6), label, fill='white')
sheet.save(F / (name + '_comparison.png'))
inputs = [P/'references'/(name+'.png'), P/'references/gdtyl.png', P/'references/gstyl.png',
          M/'materials/grey_dirt.png', M/'materials/grey_stone.png', F/'raw'/(name+'.png'),
          F/'inputs'/(name+'_native.png'), F/'prompts'/(name+'.txt'), OUT/(name+'.png')]
report = dict(status='pilot_only_requires_visual_review',
              inputs={str(p.relative_to(P)):sha(p) for p in inputs},
              runtime_sha256=sha(F/'runtime_pilot'/(name+'.png')),
              protected_border_pixels=16, flow_max=float(np.linalg.norm(flow, axis=2).max()))
(F/(name+'_pilot.json')).write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
