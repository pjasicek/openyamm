"""Quick palette/mask calibration from processed standing art, before generating actions."""
import argparse
import json
from PIL import Image, ImageDraw
from prepare_family import load, native
from process_family import mask, ramps, recolor
from package_family import overlay


def run(family):
    root, config, inv = load(family)
    vectors = ramps(config, inv)
    names = json.loads((root / 'batches.json').read_text())['standing']['frames']
    canvas = inv['logical_canvas']
    cw, ch = canvas[0] + 16, canvas[1] + 32
    out = Image.new('RGB', (len(names) * cw, 5 * ch), (48, 50, 48))
    draw = ImageDraw.Draw(out)
    for i, name in enumerate(names):
        im = Image.open(root / f'aligned_2x/{name}.png')
        coverage = mask(im, config)
        images = [native(name, config['base_palette'], canvas)]
        images += [recolor(im, coverage, int(p), config, vectors) for p in inv['variants']]
        images += [overlay(im, coverage)]
        labels = ['Native base', *inv['variants'], 'Mask']
        for j, (art, label) in enumerate(zip(images, labels)):
            if j:
                art = art.convert('RGBa').resize((round(art.width/2), round(art.height/2)),
                    Image.Resampling.LANCZOS).convert('RGBA')
            out.paste(art, (i*cw+8, j*ch+26), art)
            draw.text((i*cw+4, j*ch+4), f'{label}: {name}', fill='white')
    out.save(root / 'review/standing_calibration.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('family')
    run(parser.parse_args().family)
