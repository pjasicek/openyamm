"""Measure native/AI head and ground landmarks for explicit, reviewable sprite registration."""
from pathlib import Path
import json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]


def native_image(name):
    im = Image.open(REPO / 'assets_dev/engine/sprites' / (name + '.bmp'))
    rgba = im.convert('RGBA')
    rgba.putalpha(Image.fromarray(np.where(np.array(im) != 0, 255, 0).astype('uint8')))
    return rgba


def landmarks(im):
    a = np.array(im).astype(float)
    r, g, b, alpha = a.transpose(2, 0, 1)
    skin = (alpha > 128) & (r > b * 1.18) & (g > b * 1.25) & (r < g * 1.6)
    labels, count = ndimage.label(skin)
    sizes = np.bincount(labels.ravel())
    skin &= sizes[labels] > max(4, im.width * im.height * 0.0001)
    box = im.getchannel('A').getbbox()
    # Head is the highest substantial olive region. Keep the actual source's head movement.
    ys, xs = np.where(skin)
    top = int(ys.min())
    span = box[3] - top
    band = skin.copy()
    band[:top + round(span * .025)] = False
    band[top + round(span * .13):] = False
    ys, xs = np.where(band)
    return {'head_x': float(np.median(xs)), 'head_top': top, 'ground_y': box[3], 'alpha_bounds': box}


def build():
    groups = json.loads((ROOT / 'groups.json').read_text())
    records = {}
    preview = Image.new('RGB', (6 * 420, 6 * 400), (42, 45, 44))
    draw = ImageDraw.Draw(preview)
    i = 0
    for action, names in groups.items():
        for name in names:
            src = native_image(name)
            gen = Image.open(ROOT / 'cleaned_source' / (name + '.png'))
            if name in ['gobdyd0', 'gobdye0', 'gobdyf0']:
                sbox, gbox = src.getchannel('A').getbbox(), gen.getchannel('A').getbbox()
                sn = {'head_x': (sbox[0] + sbox[2]) / 2, 'head_top': sbox[1],
                      'ground_y': sbox[3], 'alpha_bounds': sbox}
                gn = {'head_x': (gbox[0] + gbox[2]) / 2, 'head_top': gbox[1],
                      'ground_y': gbox[3], 'alpha_bounds': gbox}
                basis = 'corpse width and native bounding-box center'
            else:
                sn, gn = landmarks(src), landmarks(gen)
                basis = 'olive head horizontal center and native silhouette ground baseline'
                # Reviewed exceptions: warm blade highlights fooled the olive detector.
                overrides = {'gobatb0': (291, 72), 'gobwid0': (271, 86), 'gobwie0': (292, 79)}
                if name in overrides:
                    gn['head_x'], gn['head_top'] = overrides[name]
                    basis += '; manually reviewed generated head landmark overrides blade highlight'
            records[name] = {'action': action, 'native': sn, 'generated': gn, 'basis': basis}
            x, y = (i % 6) * 420, (i // 6) * 400
            draw.text((x + 5, y + 5), name, fill='white')
            for j, (im, lm) in enumerate([(src, sn), (gen, gn)]):
                scale = min(200 / im.width, 350 / im.height)
                w, h = round(im.width * scale), round(im.height * scale)
                thumb = im.convert('RGBa').resize((w, h), Image.Resampling.LANCZOS).convert('RGBA')
                px, py = x + j * 210, y + 30
                preview.paste(thumb, (px, py), thumb)
                hx, hy = px + lm['head_x'] * scale, py + lm['head_top'] * scale
                gy = py + lm['ground_y'] * scale
                draw.line((hx, hy, hx, gy), fill=(255, 190, 20), width=1)
                draw.line((px, gy, px + w, gy), fill=(40, 190, 230), width=1)
            i += 1
    (ROOT / 'landmarks.json').write_text(json.dumps(records, indent=2) + '\n')
    preview.save(ROOT / 'landmark_review.png')
    print(json.dumps({n: [v['native']['head_top'], v['generated']['head_top']] for n, v in records.items()}))


if __name__ == '__main__':
    build()
