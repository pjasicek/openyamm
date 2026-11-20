"""Contact native/restored poses in one unclipped shared logical-space window."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np


def run(root):
    sources = json.loads((root / 'sources.json').read_text())['sources']
    registration = json.loads((root / 'registration.json').read_text())
    config = json.loads((root / 'config.json').read_text())
    if config.get('review_mass_region'):
        for name, record in registration.items():
            images = [Image.open(root/f'native/{name}.png').convert('RGBA'),
                      Image.open(root/f'aligned_2x/{name}.png').convert('RGBA')]
            points = []
            for im in images:
                a = np.array(im).astype(float)
                rgb, alpha = a[:, :, :3], a[:, :, 3]
                visible = alpha >= 128
                if config['review_mass_region'] == 'charcoal_torso':
                    r, g, b = np.moveaxis(rgb, -1, 0)
                    selected = visible & (rgb.max(axis=2) < 120) & ((g-np.maximum(r,b)) < 3)
                elif config['review_mass_region'] == 'olive_torso':
                    r, g, b = np.moveaxis(rgb, -1, 0)
                    selected = visible & (((g-b)-1.4*(r-g))/np.maximum(r,1) > .08) & (rgb.max(axis=2)>20)
                elif config['review_mass_region'] in ('gel_body', 'silhouette_mass'):
                    selected = visible
                else:
                    raise ValueError(config['review_mass_region'])
                ys, xs = np.where(selected)
                assert len(xs), name
                bottom = np.where(visible)[0].max()
                foot_x = np.where(visible[bottom])[0].mean()
                points.append(([float(xs.mean()), float(ys.mean())], [float(foot_x), float(bottom+1)]))
            record['review_landmarks'] = {}
            for i, label in enumerate([config['review_mass_region'], 'baseline']):
                native, restored = points[0][i], points[1][i]
                restored = [restored[j]+record['canvas_origin_px'][j]-record['translate'][j] for j in range(2)]
                record['review_landmarks'][label] = dict(native=native, restored_before_translation=restored)
        (root/'registration.json').write_text(json.dumps(registration, indent=2)+'\n')
    bounds = [r['visible_bounds'] for r in sources.values()]
    for name, record in registration.items():
        box = Image.open(root / f'aligned_2x/{name}.png').getbbox()
        origin = record['canvas_origin_px']
        bounds.append([(box[i]+origin[i % 2])/2 for i in range(4)])
    window = [math.floor(min(b[i] for b in bounds))-8 if i < 2
              else math.ceil(max(b[i] for b in bounds))+8 for i in range(4)]
    width, height = window[2]-window[0], window[3]-window[1]
    row_height = height*2+42
    names = list(registration)
    contact = Image.new('RGB', (width*4, math.ceil(len(names)/4)*row_height), (42, 42, 42))
    draw = ImageDraw.Draw(contact)
    for i, name in enumerate(names):
        origin = registration[name]['canvas_origin_px']
        native = Image.open(root / f'native/{name}.png').crop(window)
        restored = Image.open(root / f'aligned_2x/{name}.png').crop(
            [window[j]*2-origin[j % 2] for j in range(4)])
        restored = restored.convert('RGBa').resize(native.size, Image.Resampling.LANCZOS).convert('RGBA')
        x, y = i % 4*width, i//4*row_height
        for row, (sprite, background, offset) in enumerate([(native,(42,42,42),20), (restored,(230,230,230),height+32)]):
            tile = Image.new('RGB', native.size, background)
            tile.paste(sprite, mask=sprite.getchannel('A'))
            contact.paste(tile,(x,y+offset))
            if registration[name].get('review_landmarks'):
                draw.line((x+128-window[0], y+offset, x+128-window[0], y+offset+height-1), fill=(150,90,90))
                for label, point in registration[name]['review_landmarks'].items():
                    px, py = point['native'] if row == 0 else [
                        (point['restored_before_translation'][j]+registration[name]['translate'][j])/2 for j in range(2)]
                    px, py = x+px-window[0], y+offset+py-window[1]
                    color = (0,170,200) if label != 'baseline' else (190,100,40)
                    draw.line((px-3,py,px+3,py), fill=color)
                    draw.line((px,py-3,px,py+3), fill=color)
        draw.text((x+3,y+3),name+' native / restored',fill='white')
    contact.save(root / 'review/all_comparison.png')
    for i, y in enumerate(range(0,contact.height,row_height*5)):
        contact.crop((0,y,contact.width,min(y+row_height*5,contact.height))).save(root/f'review/comparison_{i}.png')
    (root/'review/contact_settings.json').write_text(json.dumps(dict(window=window,row_height=row_height),indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=Path, required=True)
    run(parser.parse_args().project)
