"""Recheck staged original crops against complete retained raw subjects."""
import json
from collections import Counter
from urllib.parse import unquote

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from prepare import HERE, OUT, PREVIOUS, read, write


def main():
    catalog = json.loads((HERE/'catalog.js').read_text().split('=', 1)[1].strip().rstrip(';'))
    assets = {a['id']: a for a in catalog['assets'].values()}
    stage = read(OUT/'stage_manifest.json')['records']
    before = read(PREVIOUS/'review.original.json')['decisions']
    repairs = read(PREVIOUS/'repairs.json')['results']
    raw_cache = {}
    audit = {}
    for target, record in stage.items():
        if 'staged_path' not in record:
            continue
        a = assets[target]
        prior = repairs.get(target)
        if prior and prior['sha256'] == record['reviewed_sha256']:
            audit[target] = {'status': 'reviewed_prior_repair', 'operations': prior['operations']}
            continue
        choice = next((c for c in a['preparedAlternatives'] if c['sha256'] == record['reviewed_sha256']), {})
        if not choice.get('rawRect') or not choice.get('raw'):
            audit[target] = {'status': 'no_raw_rectangle', 'path': record['reviewed_path']}
            continue
        raw_path = (HERE/unquote(choice['raw'])).resolve()
        if raw_path not in raw_cache:
            raw = Image.open(raw_path).convert('RGBA')
            p = np.asarray(raw).astype(float)
            mask = p[:, :, 3] > 96
            corners = p[[0, 0, -1, -1], [0, -1, 0, -1]]
            if np.median(corners[:, 3]) > 128 and np.median(corners[:, 1]) < 100:
                mask &= (np.minimum(p[:, :, 0], p[:, :, 2])-p[:, :, 1] < 80) | (np.minimum(p[:, :, 0], p[:, :, 2]) < 150)
            labels, _ = ndimage.label(mask)
            raw_cache[raw_path] = labels, np.bincount(labels.ravel()), raw.size
        labels, sizes, size = raw_cache[raw_path]
        x, y, right, bottom = choice['rawRect']
        inside = np.bincount(labels[y:bottom, x:right].ravel(), minlength=len(sizes))
        inside[0] = 0
        label = int(inside.argmax())
        total = int(sizes[label])
        lost = int(total - inside[label])
        yy, xx = np.where(labels == label)
        bounds = [int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)]
        suspect = lost > max(30, total * .003)
        audit[target] = {'status': 'inspect_clipped_raw' if suspect else 'complete_raw_subject',
                         'raw': str(raw_path), 'raw_crop': choice['rawRect'], 'subject_bounds': bounds,
                         'raw_size': size, 'lost_subject_pixels': lost, 'lost_fraction': lost/total,
                         'existing_repair_available': bool(prior)}
    write(OUT/'staged_crop_audit.json', {'targets': audit, 'summary': dict(Counter(r['status'] for r in audit.values()))})
    print(read(OUT/'staged_crop_audit.json')['summary'])
    print('New clipping suspects:', [assets[t]['name'] for t, r in audit.items()
                                      if r['status'] == 'inspect_clipped_raw' and not r['existing_repair_available']])
    names = [t for t, r in stage.items() if 'staged_path' in r and t not in before]
    (OUT/'staged_contacts').mkdir(exist_ok=True)
    for start in range(0, len(names), 20):
        sheet = Image.new('RGB', (1500, 1400), '#56646b')
        draw = ImageDraw.Draw(sheet)
        for i, target in enumerate(names[start:start+20]):
            a = assets[target]
            x, y = i % 5 * 300, i // 5 * 350
            draw.text((x+5, y+5), a['name']+'  native / staged', fill='white')
            for j, path in enumerate([a['native'], stage[target]['staged_path']]):
                im = Image.open(HERE/unquote(path)).convert('RGBA')
                if j == 0:
                    im = im.resize((im.width*2, im.height*2), Image.Resampling.NEAREST)
                im.thumbnail((145, 320), Image.Resampling.LANCZOS)
                sheet.paste(im, (x+j*150, y+25), im)
        sheet.save(OUT/'staged_contacts'/f'{start//20+1:02}.png')


if __name__ == '__main__':
    main()
