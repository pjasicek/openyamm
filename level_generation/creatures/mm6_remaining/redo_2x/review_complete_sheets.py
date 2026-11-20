"""Compose native-size pose comparisons without fitting or hiding placement differences."""
import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

from prepare_packed_outline import REPO, native_2x


def contacts(project):
    root = REPO / project
    out = root / 'redo_2x'
    sources = json.loads((root / 'sources.json').read_text())
    run = json.loads((out / 'run.json').read_text())
    registration = json.loads((out / 'registration.json').read_text())
    canvas = sources['logical_canvas']
    panels, reviewed = [], set()
    jobs = list(run['jobs'])
    sheet_names = {name for job in jobs if job.get('selected_raw') or job.get('retained_native_frames')
                   for name in job['frames']}
    aliases = sorted(set(registration) - sheet_names)
    if aliases:
        jobs.append(dict(id='native_reuse_aliases', selected_raw=True, frames=aliases))
    for job in jobs:
        if not (job.get('selected_raw') or job.get('retained_native_frames')) or not all(
                name in registration for name in job['frames']):
            continue
        originals, restored, bounds = [], [], []
        for name in job['frames']:
            native, _ = native_2x(sources['sources'][name], sources, sources['base_palette'])
            enhanced = Image.open(out / 'aligned_2x' / (name + '.png')).convert('RGBA')
            origin = registration[name]['canvas_origin_px']
            originals.append(native)
            restored.append(enhanced)
            bounds.append([v / 2 for v in native.getbbox()])
            box = enhanced.getbbox()
            bounds.append([(box[i] + origin[i % 2]) / 2 for i in range(4)])
        crop = [math.floor(min(b[0] for b in bounds)) - 8, math.floor(min(b[1] for b in bounds)) - 8,
                math.ceil(max(b[2] for b in bounds)) + 8, math.ceil(max(b[3] for b in bounds)) + 8]
        width, height = crop[2] - crop[0], crop[3] - crop[1]
        columns = max(1, min(3, 1800 // (width * 2 + 10)))
        rows = math.ceil(len(job['frames']) / columns)
        panel = Image.new('RGB', ((width * 2 + 10) * columns, (height + 28) * rows + 28), (40, 43, 41))
        draw = ImageDraw.Draw(panel)
        draw.text((5, 4), job['id'] + ' | each pair: native left, restored right | native logical size', fill='white')
        for index, name in enumerate(job['frames']):
            record = registration[name]
            x = (index % columns) * (width * 2 + 10)
            y = (index // columns) * (height + 28) + 28
            origin = record['canvas_origin_px']
            native = originals[index].crop(tuple(v * 2 for v in crop))
            enhanced = restored[index].crop((crop[0] * 2 - origin[0], crop[1] * 2 - origin[1],
                                               crop[2] * 2 - origin[0], crop[3] * 2 - origin[1]))
            for side, image in enumerate((native, enhanced)):
                rendered = (image.resize((width, height), Image.Resampling.NEAREST) if side == 0 else
                            image.convert('RGBa').resize((width, height), Image.Resampling.LANCZOS).convert('RGBA'))
                px = x + side * (width + 4)
                panel.paste(rendered, (px, y), rendered)
                axis = px + canvas[0] / 2 - crop[0]
                if px <= axis < px + width:
                    draw.line((axis, y, axis, y + height - 1), fill=(120, 55, 55))
                for label, point in record.get('review_landmarks', {}).items():
                    logical = point['native'] if side == 0 else [
                        (point['restored_before_translation'][i] + record['translate'][i]) / 2 for i in range(2)]
                    mx, my = px + logical[0] - crop[0], y + logical[1] - crop[1]
                    draw.line((mx - 3, my, mx + 3, my), fill=(30, 245, 245))
                    draw.line((mx, my - 3, mx, my + 3), fill=(30, 245, 245))
            draw.text((x + 3, y + height + 3), str(index + 1) + ': ' + name, fill='white')
            reviewed.add(name)
        panels.append((job['id'], panel))
    pages, placements = [], []
    page = Image.new('RGB', (1800, 1800), (40, 43, 41))
    x = y = row_height = 0
    used = False
    for label, panel in panels:
        if panel.width > 1800 or panel.height > 1800:
            # Large original creatures stay at native size; never shrink them to pass review.
            path = out / 'review' / (label + '_native_size_pairs.png')
            panel.save(path)
            pages.append(str(path.relative_to(out)))
            continue
        if x + panel.width > 1800:
            x, y, row_height = 0, y + row_height, 0
        if y + panel.height > 1800:
            path = out / 'review' / ('complete_placement_%02d.png' % len(placements))
            page.crop((0, 0, 1800, y + row_height)).save(path)
            pages.append(str(path.relative_to(out)))
            placements.append(path)
            page = Image.new('RGB', (1800, 1800), (40, 43, 41))
            x = y = row_height = 0
            used = False
        page.paste(panel, (x, y))
        x += panel.width
        row_height = max(row_height, panel.height)
        used = True
    if used:
        path = out / 'review' / ('complete_placement_%02d.png' % len(placements))
        page.crop((0, 0, 1800, y + row_height)).save(path)
        pages.append(str(path.relative_to(out)))
    coverage = dict(status='visual_review_pending', native_logical_scale=1, frames=sorted(reviewed),
                    jobs=[label for label, _ in panels], pages=pages,
                    method='One shared actor-local crop per complete animation/view; preserve native and restored placement, proportions and chronology. No pose fitting.')
    (out / 'review/complete_placement.json').write_text(json.dumps(coverage, indent=2) + '\n')
    print(json.dumps(dict(project=project, frames=len(reviewed), jobs=len(panels), pages=pages)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    contacts(parser.parse_args().project)
