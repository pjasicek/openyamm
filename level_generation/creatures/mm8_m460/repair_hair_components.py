"""Extend only visually identified clipped hair components, retaining before/after evidence."""
import argparse
import json
import numpy as np
from PIL import Image, ImageDraw
import materials
from process import ROOT, queue, save
from process_compact import variants

parser = argparse.ArgumentParser()
parser.add_argument('names', nargs='+')
parser.add_argument('--note', required=True)
parser.add_argument('--seed-box', nargs=4, type=int,
                    help='Reviewed enhanced-art hair seed rectangle; use with exactly one frame')
args = parser.parse_args()
assert not args.seed_box or len(args.names) == 1
path = ROOT / 'hair_component_extensions.json'
extensions = json.loads(path.read_text())
for name in args.names:
    assert name not in extensions, 'Already revised; inspect existing evidence instead'
    master = ROOT / 'toned_2x' / (name + '.png')
    im = Image.open(master).convert('RGBA')
    old = np.array(Image.open(ROOT / 'masks_2x' / (name + '.png')))
    checkpoint = ROOT / 'checkpoints/hair_masks_before' / (name + '.png')
    assert not checkpoint.exists()
    Image.fromarray(old).save(checkpoint)
    extensions[name] = {'master_sha256': queue.sha(master), 'reason': args.note,
                        'evidence': 'review/' + name + '_hair_revision.png'}
    if args.seed_box:
        extensions[name]['hair_seed_box'] = args.seed_box
    save(path, extensions)
    settings = materials.settings()
    new = materials.masks(im, settings, name)
    assert np.array_equal(old[:, :, 0], new[:, :, 0])
    changed = np.any(old != new, axis=2)
    assert changed.any()
    ys, xs = np.where(changed)
    box = [max(0, int(xs.min()) - 30), max(0, int(ys.min()) - 30),
           min(576, int(xs.max()) + 31), min(576, int(ys.max()) + 31)]
    overlay = np.array(im)
    overlay[changed, :3] = [255, 70, 30]
    pictures = [im, materials.recolor(im, old, 463, settings),
                materials.recolor(im, new, 463, settings), Image.fromarray(overlay)]
    sheet = Image.new('RGB', (1200, 320), (90, 90, 90))
    draw = ImageDraw.Draw(sheet)
    for i, (label, picture) in enumerate(zip(['base', 'before', 'after', 'changed mask'], pictures)):
        crop = picture.crop(box)
        crop.thumbnail((296, 288))
        bg = Image.new('RGBA', crop.size, (90, 90, 90, 255))
        bg.alpha_composite(crop)
        sheet.paste(bg.convert('RGB'), (i * 300, 24))
        draw.text((i * 300 + 3, 3), name + ' ' + label, fill='white')
    sheet.save(ROOT / extensions[name]['evidence'])
    variants(name, im, settings)
    extensions[name]['changed_mask_pixels'] = int(changed.sum())
    save(path, extensions)
    save(ROOT / 'material_settings.json', materials.settings())
    print(name, int(changed.sum()), 'hair mask pixels revised; visual review required')
