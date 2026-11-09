"""Read-only installed-package and generated-sampling review; does not certify anatomical motion."""
import collections
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


sys.path.insert(0, str(HERE.parents[1]))
from mm6_sampling_audit import audit as audit_sampling


def read(path):
    return json.loads(path.read_text())


def run():
    ledger = read(HERE.parent / 'progress.json')
    installed = read(HERE.parent / 'installation.json')
    counts = collections.Counter()
    families = []
    for family in ledger['families']:
        root = (REPO / family['package']).parent
        manifest = read(root / 'manifest.json')
        runtime = read(REPO / family['installed_package'] / 'manifest.json')
        assert runtime['pixels_per_logical_pixel'] == 2
        assert set(runtime['frames']) == set(manifest['frames'])
        rows = audit_sampling(root)['frames']
        counts.update(row['status'] for row in rows)
        measured = [min(r['sampling_x'], r['sampling_y']) for r in rows if 'sampling_x' in r]
        families.append({'family': family['label'], 'package': family['package'],
                         'installed_package': family['installed_package'], 'frames': rows,
                         'counts': dict(collections.Counter(r['status'] for r in rows)),
                         'minimum_sampling': min(measured), 'maximum_sampling': max(measured)})
    mismatches = []
    files = 0
    for package in installed['packages']:
        for name, record in package['files'].items():
            path = REPO / 'assets_source/engine/sprites_new' / package['package'] / name
            files += 1
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
                mismatches.append(str(path.relative_to(REPO)))
    report = {
        'scope': 'All 60 installed MM6 families; sampling estimated from actual retained registration transforms',
        'counts': dict(counts), 'families_with_below_2x_frames': sum(f['counts'].get('below_2x', 0) > 0 for f in families),
        'source_export_files_checked': files, 'installed_hash_mismatches': mismatches,
        'runtime_tier': 'All 60 packages declare and preserve the 2x coordinate/crop contract',
        'limits': ['Sampling is raster density, not a proof of invented detail quality or correct anatomy.',
                   'Frame names include native pixel aliases; these are not independent AI generations.',
                   'This does not certify frame-by-frame anatomical landmarks or animation stability.',
                   'Earlier full-frame vertical-bound screening is not a full horizontal/vertical motion audit.'],
        'families': families,
    }
    (HERE / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'families'}, indent=2))
    lines = ['# MM6 generated-sampling inventory', '',
             'Sampling is generated raster pixels per native logical pixel, before enlargement to the 2x export.',
             'These measurements do not certify anatomical/animation alignment.', '',
             '| Family | Frames below 2x | Measured range |', '| --- | ---: | --- |']
    for f in families:
        lines.append(f"| {f['family']} | {f['counts'].get('below_2x', 0)} | "
                     f"{f['minimum_sampling']:.3f}–{f['maximum_sampling']:.3f}x |")
    (HERE / 'SAMPLING.md').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    run()
