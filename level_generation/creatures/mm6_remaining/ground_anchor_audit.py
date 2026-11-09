"""Read-only audit of native versus atlas pixels in actor-local logical coordinates."""
from pathlib import Path
import json
from collections import defaultdict
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = HERE / 'ground_anchor_review'


def bounds(alpha, threshold):
    return Image.fromarray((alpha >= threshold).astype(np.uint8)).getbbox()


def native_image(source, palette):
    im = Image.open(REPO / source['path'])
    ix = np.array(im)
    rgb = np.fromfile(palette, np.uint8)[:768].reshape(256, 3)[ix]
    return Image.fromarray(np.dstack([rgb, (ix != 0).astype(np.uint8) * 255]))


def atlas_image(root, manifest, frame, pages):
    index = frame['page']
    if index not in pages:
        pages[index] = Image.open(root / manifest['pages'][index]['base']).convert('RGBA')
    x, y, w, h = frame['atlas_xywh']
    return pages[index].crop((x, y, x + w, y + h))


def run():
    OUT.mkdir(exist_ok=True)
    ledger = json.loads((HERE / 'progress.json').read_text())
    families = []
    all_rows = []
    contacts = []
    for family in ledger['families']:
        root = (REPO / family['package']).parent
        manifest = json.loads((root / 'manifest.json').read_text())
        sources = json.loads((root / 'sources.json').read_text())['sources']
        tier = manifest['pixels_per_logical_pixel']
        pivot = manifest['logical_pivot']
        canvas = manifest['logical_canvas']
        membership = defaultdict(set)
        for action, animation in manifest['animations'].items():
            for view, sequence in animation.get('views', {}).items():
                for step in sequence:
                    if step.get('frame'):
                        membership[step['frame']].add(action)
        pages = {}
        rows = []
        for name, frame in manifest['frames'].items():
            source = sources[name]
            native = Image.open(REPO / source['path'])
            a = (np.array(native) != 0).astype(np.uint8) * 255
            b = np.array(atlas_image(root, manifest, frame, pages))[:, :, 3]
            is_center = manifest.get('anchor') == 'center'
            native_pivot_y = native.height / 2 if is_center else native.height
            offset = frame.get('native_offset', [0, 0])
            expected_offset_y = (canvas[1] - native.height) / (2 if is_center else 1)
            crop = frame['crop_origin_px']
            row = dict(family=family['label'], package=family['package'], frame=name,
                       actions=sorted(membership[name]), anchor=manifest.get('anchor'),
                       native_offset_y_error=offset[1] - expected_offset_y,
                       pivot_y_error=pivot[1] - canvas[1] / (2 if is_center else 1),
                       thresholds={})
            for threshold in (16, 96, 128, 224):
                nb, eb = bounds(a, threshold), bounds(b, threshold)
                if nb is None or eb is None:
                    row['thresholds'][str(threshold)] = dict(native_empty=nb is None, enhanced_empty=eb is None)
                    continue
                native_up = native_pivot_y - nb[3]
                enhanced_up = pivot[1] - (crop[1] + eb[3]) / tier
                row['thresholds'][str(threshold)] = dict(native_bottom_up=native_up,
                    enhanced_bottom_up=enhanced_up, lift=enhanced_up-native_up,
                    native_height=nb[3]-nb[1], enhanced_height=(eb[3]-eb[1])/tier)
            rows.append(row)
        all_rows.extend(rows)
        active = [r for r in rows if set(r['actions']) & {'standing', 'walk'} and 'lift' in r['thresholds']['128']]
        worst = sorted(active, key=lambda r: r['thresholds']['128']['lift'], reverse=True)
        summary = dict(family=family['label'], package=family['package'], frames=len(rows),
                       standing_walk_frames=len(active),
                       min_lift=min(r['thresholds']['128']['lift'] for r in active),
                       max_lift=max(r['thresholds']['128']['lift'] for r in active),
                       frames_lift_over_2=[r['frame'] for r in active if r['thresholds']['128']['lift'] > 2],
                       origin_errors=[r['frame'] for r in rows if r['pivot_y_error'] or r['native_offset_y_error']])
        families.append(summary)
        standing = next(r for r in active if 'standing' in r['actions'])
        choices = [standing, next((r for r in worst if r['frame'] != standing['frame']), standing)]
        # Same actor origin and scale on both sides; crop padding is never used as the origin.
        panel = Image.new('RGB', (1000, 380), (43, 46, 43))
        draw = ImageDraw.Draw(panel)
        draw.text((8, 5), family['label'] + ' | native / atlas; cyan = actor origin', fill='white')
        for slot, row in enumerate(choices):
            frame = manifest['frames'][row['frame']]
            source = sources[row['frame']]
            pal = frame['source_palette']
            palette = REPO / f'assets_dev/worlds/mm6/textures/pal{pal}.act'
            if not palette.exists():
                palette = REPO / f'assets_dev/engine/terrain/pal{pal}.act'
            original = native_image(source, palette)
            enhanced = atlas_image(root, manifest, frame, pages)
            scale = min(1.05, 275 / max(canvas[1], 1), 210 / max(canvas[0], 1))
            baseline = 325 if manifest.get('anchor') != 'center' else 205
            for side, image in enumerate((original, enhanced)):
                center = slot * 500 + side * 250 + 125
                draw.line((center-118, baseline, center+118, baseline), fill=(90, 185, 190))
                draw.line((center, baseline-5, center, baseline+5), fill=(90, 185, 190))
                if side == 0:
                    x = -original.width / 2
                    y = -(original.height / 2 if manifest.get('anchor') == 'center' else original.height)
                    physical_scale = scale
                else:
                    x = frame['crop_origin_px'][0] / tier - pivot[0]
                    y = frame['crop_origin_px'][1] / tier - pivot[1]
                    physical_scale = scale / tier
                resized = image.convert('RGBa').resize((max(1, round(image.width*physical_scale)),
                          max(1, round(image.height*physical_scale))), Image.Resampling.LANCZOS).convert('RGBA')
                panel.paste(resized, (round(center+x*scale), round(baseline+y*scale)), resized)
            draw.text((slot*500+8, 343), row['frame'] + ' ' + '/'.join(row['actions']), fill='white')
            draw.text((slot*500+8, 359), 'lift at alpha128: %.1f native px' % row['thresholds']['128']['lift'], fill='white')
        contacts.append(panel)
        print(family['label'], summary['min_lift'], summary['max_lift'], flush=True)
    for index in range(0, len(contacts), 6):
        sheet = Image.new('RGB', (2000, 1140))
        for slot, panel in enumerate(contacts[index:index+6]):
            sheet.paste(panel, ((slot % 2)*1000, (slot // 2)*380))
        sheet.save(OUT / ('families_%02d.png' % (index//6+1)))
    report = dict(scope='All 60 staged MM6 packages, actual atlas pixels versus native BMP index-zero alpha',
                  units='Native logical pixels before native actor/frame scale; positive lift means higher',
                  warning='Lowest visible pixel is a screening metric, not necessarily a foot; visuals determine contact',
                  family_count=len(families), frame_count=len(all_rows), families=families, frames=all_rows)
    (OUT / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    run()
