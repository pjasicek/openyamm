"""Compact every-pose variant contact for explicit visual review, never automatic acceptance."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw


def main(project, candidates=False):
    root = Path(project).resolve()/'redo_2x'
    # Partial candidates have no exported configuration/package yet. Select their
    # authoritative preparation explicitly rather than falling back from a stale export.
    source = root.parent if candidates else root
    config = json.loads((source/'config.json').read_text())
    if config.get('material_module'):
        spec = importlib.util.spec_from_file_location('review_materials', source/config['material_module'])
        materials = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(materials)
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'mm6_peasants'))
        import process_family as materials
    vectors = {int(k): v for k, v in json.loads((source/'recolor_vectors.json').read_text()).items()}
    registration = json.loads((root/'registration.json').read_text())
    names = list(registration)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'mm6_peasants'))
    from package_family import frame_recolor_vectors, overlay
    _, frame_vectors = frame_recolor_vectors(source, names, vectors)
    palettes = [int(p) for p in config['variant_names']]
    for page in range((len(names)+15)//16):
        sheet = Image.new('RGB', (1600, 1200), (45, 45, 45))
        draw = ImageDraw.Draw(sheet)
        for i, name in enumerate(names[page*16:page*16+16]):
            image = Image.open(root/'aligned_2x'/(name+'.png'))
            mask = Image.open(root/'masks_2x'/(name+'.png'))
            box = image.getbbox()
            x, y = (i % 4)*400, (i//4)*300
            draw.text((x, y+5), name, fill='white')
            for j, palette in enumerate(palettes):
                variant = materials.recolor(image, mask, palette, config, frame_vectors.get(name, vectors)).crop(box)
                variant.thumbnail((128, 265))
                sheet.paste(variant, (x+j*132, y+30), variant)
        sheet.save(root/'review'/('all_variants_%d.png'%page))
    if candidates:
        sheet = Image.new('RGB', (1440, ((len(names)+7)//8)*180), '#e6e6e3')
        draw = ImageDraw.Draw(sheet)
        for i, name in enumerate(names):
            image = Image.open(root/'aligned_2x'/(name+'.png')).convert('RGBA')
            coverage = Image.open(root/'masks_2x'/(name+'.png'))
            image = overlay(image, coverage).crop(image.getbbox())
            image.thumbnail((170, 150))
            x, y = (i%8)*180, (i//8)*180
            sheet.paste(image, (x+5, y+25), image)
            draw.text((x+4, y+5), name, fill='black')
        sheet.save(root/'review/all_masks_light.png')
    print('Rendered', len(names), 'poses across', len(palettes), 'native palettes.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('--candidates', action='store_true', help='Review registered partial candidates without export')
    args = parser.parse_args()
    main(args.project, args.candidates)
