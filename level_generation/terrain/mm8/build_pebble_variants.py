"""Register generated pebble details and insert only native variant regions over the dirt master."""
import json
import cv2
from scipy.ndimage import binary_dilation, gaussian_filter
from common import *
from PIL import ImageDraw


def main():
    folder = P / 'variants/v1'
    native_base = read(P / 'references/dirttyl.png')
    master = read(M / 'materials/dirt.png')
    yy, xx = np.mgrid[:512, :512].astype('float32')
    records = {}
    sheet = Image.new('RGB', (1024, 560), '#202933')
    draw = ImageDraw.Draw(sheet)
    for row, name in enumerate(('dirt1', 'dirt2')):
        source = read(P / 'references' / (name + '.png'))
        original = read(P / 'references' / (name + '.png'), 512)
        ai = read(folder / 'raw' / (name + '.png'), 512)
        changed = binary_dilation(np.max(abs(source - native_base), axis=2) > 3, iterations=2)
        alpha = np.asarray(Image.fromarray(changed.astype('float32')).resize((512, 512), Image.Resampling.BICUBIC), float)
        alpha = gaussian_filter(np.clip(alpha, 0, 1), 1)
        flow = cv2.calcOpticalFlowFarneback(cv2.cvtColor(seams.byte(original), cv2.COLOR_RGB2GRAY),
                                          cv2.cvtColor(seams.byte(ai), cv2.COLOR_RGB2GRAY),
                                          None, .5, 4, 41, 7, 7, 1.5, 0)
        ai = cv2.remap(ai.astype('float32'), xx + flow[:, :, 0], yy + flow[:, :, 1],
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        # Tone only the stone+contact regions, without reintroducing AI earth into the rest of the tile.
        selected = alpha > .5
        target, sample = original[selected], ai[selected]
        ai = np.clip((ai - sample.mean(0)) * np.clip(target.std(0) / np.maximum(sample.std(0), 1), .65, 1.35)
                     + target.mean(0), 0, 255)
        border = np.minimum.reduce([xx, yy, 511 - xx, 511 - yy])
        alpha *= np.clip((border - 8) / 16, 0, 1)
        pixels = seams.srgb(seams.linear(master) * (1 - alpha[:, :, None]) + seams.linear(ai) * alpha[:, :, None])
        save(folder / 'authoring' / (name + '.png'), pixels)
        save(folder / 'masks' / (name + '.png'), alpha * 255)
        save(OUT / (name + '.png'), seams.reduce(seams.pad(pixels, 'wrap')))
        assert np.array_equal(pixels[alpha == 0], master[alpha == 0].astype('uint8'))
        records[name] = dict(raw_sha256=sha(folder / 'raw' / (name + '.png')),
                             prompt_sha256=sha(folder / 'prompts' / (name + '.txt')),
                             native_sha256=sha(P / 'references' / (name + '.png')),
                             mask_sha256=sha(folder / 'masks' / (name + '.png')),
                             runtime_sha256=sha(OUT / (name + '.png')),
                             protected_fraction=float(np.mean(alpha == 0)))
        for col, path in enumerate([P / 'references' / (name + '.png'), folder / 'raw' / (name + '.png'),
                                    OUT / (name + '.png'), folder / 'masks' / (name + '.png')]):
            sheet.paste(Image.open(path).convert('RGB').resize((256, 256)), (col * 256, row * 280 + 24))
            draw.text((col * 256 + 4, row * 280 + 5), name + ' ' + ['native', 'raw AI', 'composite x2', 'insertion'][col], fill='white')
    sheet.save(folder / 'comparison.png')
    (folder / 'build.json').write_text(json.dumps(dict(status='candidate_visual_review_required', tiles=records,
                                                       dirt_master_sha256=sha(M / 'materials/dirt.png')), indent=2) + '\n')
    print('Composed two pebble variants with protected master dirt')


if __name__ == '__main__':
    main()
