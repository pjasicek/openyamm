"""Render coordinate-preserving annotation panels; display fits are never registration scales."""
import hashlib
import json
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from prepare_run import REPO, native

def main(project):
    ROOT = Path(project).resolve()
    OUT = ROOT / 'redo_2x'
    run = json.loads((OUT / 'run.json').read_text())
    policy = json.loads((OUT / 'processing.json').read_text())
    selected_jobs = policy.get('selected_frame_jobs', {})
    records = {}
    for job in run['jobs']:
        if not job.get('selected_raw'):
            continue
        report = json.loads((OUT / 'review' / (job['id'] + '_extraction.json')).read_text())
        assert report['raw'] == job['selected_raw']
        for frame in report['frames']:
            name = frame['frame']
            if name in selected_jobs and selected_jobs[name] != job['id']:
                continue
            if name in records:
                continue
            records[name] = dict(job=job['id'], raw_sha256=report['raw_sha256'],
                                 clean_path=frame['clean_path'])
    names = list(records)
    for page in range((len(names) + 7) // 8):
        canvas = Image.new('RGB', (1200, 1600), (36, 39, 39))
        draw = ImageDraw.Draw(canvas)
        for index, name in enumerate(names[page * 8:page * 8 + 8]):
            record = records[name]
            origin_x, origin_y = (index % 2) * 600, (index // 2) * 400
            source = native(ROOT, name)
            raw = Image.open(REPO / record['clean_path']).convert('RGBA')
            record['page'] = page
            record['panel_origin'] = [origin_x, origin_y]
            for side, image in [('native', source), ('raw', raw)]:
                box = image.getbbox()
                cropped = image.crop(box)
                ratio = min(280 / cropped.width, 350 / cropped.height)
                size = [round(cropped.width * ratio), round(cropped.height * ratio)]
                offset = [(300 - size[0]) // 2, 35 + (350 - size[1]) // 2]
                side_x = origin_x + (300 if side == 'raw' else 0)
                rendered = cropped.resize(size, Image.Resampling.NEAREST if side == 'native'
                                          else Image.Resampling.LANCZOS)
                canvas.paste(rendered, (side_x + offset[0], origin_y + offset[1]), rendered)
                draw.text((side_x + 4, origin_y + 4), name + ' ' + side, fill='white')
                for coordinate in range(50, 300, 50):
                    draw.text((side_x + coordinate, origin_y + 20), str(coordinate), fill=(130, 150, 150))
                for coordinate in range(50, 400, 50):
                    draw.text((side_x + 1, origin_y + coordinate), str(coordinate), fill=(130, 150, 150))
                record[side] = dict(crop=list(box), display_size=size, display_offset=offset,
                                    image_size=list(image.size))
            record['clean_sha256'] = hashlib.sha256((REPO / record['clean_path']).read_bytes()).hexdigest()
        canvas.save(OUT / 'review' / ('anatomy_annotation_%02d.png' % page))
    (OUT / 'review/anatomy_annotation_layout.json').write_text(json.dumps(dict(
        status='annotation_layout_only_not_accepted_registration', frames=records), indent=2) + '\n')
    print('Prepared %d native/raw pairs; no placement or sampling accepted.' % len(records))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project', nargs='?', default=str(REPO/'level_generation/creatures/mm6_bat'))
    main(parser.parse_args().project)
