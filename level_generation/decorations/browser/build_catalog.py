"""Build the static decoration review catalog from the accepted sprite ledger."""

import hashlib
import json
import argparse
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
JOBS = REPO / 'level_generation/sprites/restoration_jobs'


def read(name):
    path = JOBS / name
    return json.loads(path.read_text()), hashlib.sha256(path.read_bytes()).hexdigest()


def browser_path(path):
    absolute = (REPO / path).resolve()
    if not absolute.is_relative_to(REPO) or not absolute.is_file():
        raise ValueError(f'Missing or external catalog image: {path}')
    return '../../../' + str(absolute.relative_to(REPO))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remaining', action='store_true', help='Build the non-decoration review catalog')
    args = parser.parse_args()
    groups, groups_hash = read('groups.json')
    sources, sources_hash = read('sources.json')
    export, export_hash = read('export.json')
    selected = []
    unavailable = []
    for group in groups:
        if args.remaining and group['category'] == 'decorations':
            continue
        if not args.remaining and group['category'] != 'decorations':
            continue
        tracks = []
        unavailable_reason = None
        for track in group['tracks']:
            timeline = []
            for frame in track['timeline']:
                asset = frame['asset']
                if asset is None:
                    continue
                source = sources[asset]
                exported = export['frames'].get(asset)
                if not exported or 'file' not in exported:
                    if source.get('keep_native'):
                        unavailable_reason = source['keep_native']
                        continue
                    if asset in export['user_excluded_assets']:
                        unavailable_reason = 'User excluded; keep native'
                        continue
                    raise ValueError(f'{group["name"]}: {asset} lacks a restored output')
                timeline.append({
                    'index': frame['index'],
                    'image': frame['image'],
                    'asset': asset,
                    'native': browser_path(JOBS.relative_to(REPO) / source['native']),
                    'restored': browser_path(exported['file']),
                    'native_size': source['native_size'],
                    'duration_ms': max(20, frame['duration_ms']),
                    'mirrored': frame['mirrored'],
                })
            if timeline:
                tracks.append({'octants': track['octants'], 'frames': timeline})
        if not tracks or unavailable_reason:
            entry = {'sprite_id': group['sprite_id'], 'name': group['name'],
                     'missing_images': group['missing_images']}
            if args.remaining:
                entry['reason'] = unavailable_reason or 'No native artwork'
            unavailable.append(entry)
            continue
        entry = {
                'sprite_id': group['sprite_id'],
                'name': group['name'],
                'label': group['label'],
                'profile': group['profile'],
                'missing_images': group['missing_images'],
                'tracks': tracks,
        }
        if args.remaining:
            entry['category'] = group['category']
        selected.append(entry)
    selected.sort(key=lambda group: (group['name'] == 'pending', group['sprite_id']))
    payload = {
        'schema': 'openyamm.sprite_review_browser.v1' if args.remaining else 'openyamm.decoration_browser.v1',
        'source_sha256': {'groups': groups_hash, 'sources': sources_hash, 'export': export_hash},
        'groups' if args.remaining else 'decorations': selected,
        'unavailable': unavailable,
    }
    target = HERE / ('remaining_catalog.js' if args.remaining else 'catalog.js')
    variable = 'SPRITE_REVIEW_CATALOG' if args.remaining else 'DECORATION_CATALOG'
    contents = f'window.{variable} = ' + json.dumps(payload, separators=(',', ':')) + ';\n'
    if not target.exists() or target.read_text() != contents:
        target.write_text(contents)
    print(f'{target}: {len(selected)} groups, '
          f'{sum(len(t["frames"]) for g in selected for t in g["tracks"])} timeline frames, '
          f'{len(unavailable)} without native artwork')


if __name__ == '__main__':
    main()
