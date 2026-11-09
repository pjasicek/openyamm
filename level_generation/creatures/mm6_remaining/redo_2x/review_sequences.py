"""Render sequence overviews and native-size placement contacts with actual landmark markers."""
import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

from prepare_run import native


def placement_contacts(action, view, names, sources, restored, registration, manifest, output):
    # Use both silhouettes in actor-local coordinates so a bad translation cannot disappear outside the crop.
    boxes = [im.getbbox() for im in sources]
    for name, im in zip(names, restored):
        box = im.getbbox()
        origin = registration[name]['canvas_origin_px']
        boxes.append([(box[i] + origin[i % 2]) / 2 for i in range(4)])
    crop = [math.floor(min(b[0] for b in boxes))-8, math.floor(min(b[1] for b in boxes))-8,
            math.ceil(max(b[2] for b in boxes))+8, math.ceil(max(b[3] for b in boxes))+8]
    width, height = crop[2]-crop[0], crop[3]-crop[1]
    columns = max(1, min(4, 1400 // width))
    pivot = manifest['logical_pivot']
    annotated = set()
    for start in range(0, len(names), columns):
        selected = names[start:start+columns]
        panel = Image.new('RGB', (width*len(selected), height*2+72), (40, 42, 41))
        draw = ImageDraw.Draw(panel)
        draw.text((4, 2), action+' view '+view+' | native above, restored below | cyan: detected landmarks', fill='white')
        for column, name in enumerate(selected):
            index = start + column
            record = registration[name]
            origin, translation = record['canvas_origin_px'], record['translate']
            points = dict(record.get('review_landmarks', {}))
            legacy = record.get('placement_landmarks', {})
            if 'native_crown' in legacy and 'restored_crown_before_translation' in legacy:
                points.setdefault('crown', dict(native=legacy['native_crown'],
                    restored_before_translation=legacy['restored_crown_before_translation']))
            if points:
                annotated.add(name)
            for row in range(2):
                x, y = column*width, 26+row*(height+22)
                if row == 0:
                    tile = sources[index].crop(crop)
                else:
                    tile = restored[index].crop((crop[0]*2-origin[0], crop[1]*2-origin[1],
                                                crop[2]*2-origin[0], crop[3]*2-origin[1]))
                    tile = tile.convert('RGBa').resize((width, height), Image.Resampling.LANCZOS).convert('RGBA')
                panel.paste(tile, (x, y), tile)
                px, py = x+pivot[0]-crop[0], y+pivot[1]-crop[1]
                if x <= px < x+width:
                    draw.line((px, y, px, y+height-1), fill=(150, 65, 65))
                if y <= py < y+height:
                    draw.line((x, py, x+width-1, py), fill=(150, 65, 65))
                for label, point in points.items():
                    logical = point['native'] if row == 0 else [
                        (point['restored_before_translation'][i]+translation[i])/2 for i in range(2)]
                    mx, my = x+logical[0]-crop[0], y+logical[1]-crop[1]
                    draw.line((mx-4, my, mx+4, my), fill=(40, 255, 255))
                    draw.line((mx, my-4, mx, my+4), fill=(40, 255, 255))
                    draw.text((mx+5, my), label, fill=(40, 255, 255))
                draw.text((x+3, y+height+2), name+(' (no saved landmarks)' if not points else ''), fill='white')
        panel.save(output/('placement_%s_%s_%02d.png' % (action, view, start//columns)))
    return annotated


def main(project, output_dir=None, staged_root=None):
    root = Path(project).resolve()
    out = Path(staged_root).resolve() if staged_root else root/'redo_2x'
    output = Path(output_dir).resolve() if output_dir else out/'review'
    output.mkdir(parents=True, exist_ok=True)
    registration = json.loads((out/'registration.json').read_text())
    manifest = json.loads((root/'manifest.json').read_text())
    sequences, seen = [], set()
    for action, record in manifest['animations'].items():
        for view, steps in record['views'].items():
            if int(view) > 4:
                continue
            names = tuple(step['frame'] for step in steps)
            if not names:
                continue
            if names not in seen:
                seen.add(names)
                sequences.append((action, view, names))
    annotated, reviewed = set(), set()
    for action, view, names in sequences:
        sources = [native(root, name) for name in names]
        restored = [Image.open(out/'aligned_2x'/(name+'.png')).convert('RGBA') for name in names]
        annotated.update(placement_contacts(action, view, names, sources, restored, registration, manifest, output))
        reviewed.update(names)
    columns = max(len(names) for _, _, names in sequences)
    for page in range((len(sequences)+3)//4):
        panel = Image.new('RGB', (columns*240, 1400), (40, 42, 41))
        draw = ImageDraw.Draw(panel)
        for row, (action, view, names) in enumerate(sequences[page*4:page*4+4]):
            source = [native(root, name) for name in names]
            bounds = [image.getbbox() for image in source]
            crop = [min(b[0] for b in bounds)-6, min(b[1] for b in bounds)-6,
                    max(b[2] for b in bounds)+6, max(b[3] for b in bounds)+6]
            width, height = crop[2]-crop[0], crop[3]-crop[1]
            ratio = min(230/width, 145/height)
            size = (round(width*ratio), round(height*ratio))
            draw.text((4, row*350+2), action+' view '+view+'; native above, restored below', fill='white')
            for column, (name, original) in enumerate(zip(names, source)):
                origin = registration[name]['canvas_origin_px']
                restored = Image.open(out/'aligned_2x'/(name+'.png')).convert('RGBA')
                restored = restored.crop((crop[0]*2-origin[0], crop[1]*2-origin[1],
                                          crop[2]*2-origin[0], crop[3]*2-origin[1]))
                for index, image in enumerate([original.crop(crop), restored]):
                    rendered = image.resize(size, Image.Resampling.NEAREST if index == 0
                                            else Image.Resampling.LANCZOS)
                    panel.paste(rendered, (column*240+(230-size[0])//2,
                                          row*350+25+index*160), rendered)
                draw.text((column*240+4, row*350+330), name, fill='white')
        panel.save(output/('assembled_sequences_%d.png'%page))
    print('Rendered', len(sequences), 'distinct stored-pose sequences without per-frame fitting.')
    print('Native-size placement contacts:', len(reviewed), 'frames;', len(annotated), 'with saved landmarks.')
    if reviewed - annotated:
        print('Placement review needs anatomical annotations for:', ', '.join(sorted(reviewed - annotated)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('--output-dir', help='Write review images elsewhere without changing accepted evidence')
    parser.add_argument('--staged-root', help='Inspect an archived registration and aligned masters')
    args = parser.parse_args()
    main(args.project, args.output_dir, args.staged_root)
