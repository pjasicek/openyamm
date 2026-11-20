"""Verify frozen bases, protected pixels, approvals, placements, and current candidates."""
import json
import sys
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw

from prepare import OUT, HERE, ROOT, read, js, write, digest

sys.path.insert(0, str(HERE))
from scan_magenta import measure, classify


def main():
    manifest = read(OUT / 'manifest.json')
    snapshot = js(HERE / 'acceptance_snapshot_20260926_1322/review.js')
    overlay = js(OUT / 'review.js')
    catalog = js(HERE / 'catalog.js')
    for key in ['decisions', 'placements', 'staged', 'completion_scope']:
        assert overlay[key] == snapshot[key], key
    staged = [r for r in snapshot['staged'].values() if r.get('staged_path')]
    for record in staged:
        assert digest(HERE / record['staged_path']) == record['reviewed_sha256'], record['name']
    scans = []
    for row in manifest['pairs']:
        name = row['held']
        asset = catalog['assets'][name]
        assert digest(ROOT / asset['source']) == asset['sourceHash'], name
        assert digest(HERE / row['base_path']) == row['base_sha256'], name
        assert digest(HERE / row['path']) == row['sha256'], name
        assert overlay['repairs'][row['target']]['sha256'] == row['sha256'], name
        base = np.asarray(Image.open(HERE / row['base_path']).convert('RGBA'))
        result_image = Image.open(HERE / row['path']).convert('RGBA')
        result = np.asarray(result_image)
        allowed = np.asarray(Image.open(HERE / row['mask_path'])) > 0
        assert result.shape == base.shape == (asset['size'][1]*2, asset['size'][0]*2, 4), name
        assert np.array_equal(base[~allowed], result[~allowed]), name
        if row['native_pair_identical']:
            assert not allowed.any() and row['sha256'] == row['base_sha256'], name
        else:
            # Independent coarse anatomical bound, beyond the exact-mask invariant:
            # no changed pixel may reach the opposite half or lower body.
            alpha_union = (base[:, :, 3] > 0) | (result[:, :, 3] > 0)
            yy, xx = np.where(alpha_union)
            changed = np.any(base != result, axis=2)
            cy, cx = np.where(changed)
            assert cx.max() < xx.min() + (xx.max()-xx.min()+1) * .55, name
            assert cy.max() < yy.min() + (yy.max()-yy.min()+1) * .7, name
            assert changed.sum() < alpha_union.sum() * .2, name
        native = Image.open(HERE / asset['native']).convert('RGBA')
        metrics, native_metrics = measure(result_image), measure(native)
        scans.append({'target': row['target'], 'name': name, 'candidate_hash': row['sha256'],
                      'source_hash': asset['sourceHash'], 'path': row['path'],
                      'status': classify(metrics, native_metrics), 'metrics': metrics,
                      'native_metrics': native_metrics,
                      'report': 'held_armor_20260926/magenta_scan.json'})
    assert digest(HERE.parent / 'checkpoint/state.json') == manifest['ledger_sha256']
    write(OUT / 'magenta_scan.json', {'schema': 'openyamm-magenta-screen-v1',
          'summary': dict(Counter(r['status'] for r in scans)), 'records': scans})
    edited = [r for r in manifest['pairs'] if not r['native_pair_identical']]
    if all((OUT / 'equipped' / (r['held']+'.png')).exists() for r in edited):
        for page in range((len(edited)+11)//12):
            sheet = Image.new('RGB', (1200, 1440), (50, 55, 61))
            draw = ImageDraw.Draw(sheet)
            for i, row in enumerate(edited[page*12:page*12+12]):
                image = Image.open(OUT / 'equipped' / (row['held']+'.png')).convert('RGBA')
                image = image.crop(image.getbbox())
                image.thumbnail((290, 449), Image.Resampling.LANCZOS)
                x, y = (i%4)*300, (i//4)*480
                draw.text((x+8, y+5), row['held'], fill='white')
                sheet.paste(image, (x+5, y+28), image)
            sheet.save(OUT / 'contact' / f'equipped-{page+1:02d}.png')
    report = {'result': 'PASS', 'pairs_checked': len(manifest['pairs']),
              'unchanged_staged_files_verified': len(staged),
              'exact_base_file_copies': sum(r['native_pair_identical'] for r in manifest['pairs']),
              'outside_rgba_differences': 0, 'outside_alpha_differences': 0,
              'canvas_or_origin_changes': 0, 'decisions_changed': 0, 'placements_changed': 0,
              'coarse_arm_bounds_pass': True, 'ledger_changed': False,
              'magenta_scan': dict(Counter(r['status'] for r in scans))}
    write(OUT / 'validation.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
