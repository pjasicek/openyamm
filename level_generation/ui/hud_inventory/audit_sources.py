"""Read-only source/provenance audit; never generates or installs artwork."""
import collections
import hashlib
import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RASTER = {'.bmp', '.png', '.pcx'}


def relative(path):
    return path.relative_to(ROOT).as_posix()


def pixel_hash(path):
    with Image.open(path) as image:
        image = image.convert('RGBA')
        return hashlib.sha256(str(image.size).encode() + image.tobytes()).hexdigest()


def main():
    scope = json.loads((HERE / 'scope.json').read_text())
    sources = [ROOT / 'data/Data/icons.lod']
    sources += [p for p in (ROOT / 'reference/mmerge_data_forus/Data').rglob('*')
                if p.is_dir() and 'icons' in p.name.lower() and p.name.lower().endswith('.lod')]
    by_hash = collections.defaultdict(list)
    by_name = collections.defaultdict(list)
    records = []
    for directory in sorted(sources):
        for path in sorted(directory.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in RASTER:
                continue
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            by_hash[sha].append(relative(path))
            by_name[path.stem.lower()].append((path, sha))
    print('Indexed native files:', sum(map(len, by_hash.values())), flush=True)
    pixel_cache = {}
    for row in scope['files']:
        path = ROOT / row['id']
        current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        assert current_hash == row['sha256'], f'Source drift: {row["id"]}; reconcile the census first'
        result = dict(path=row['id'], sha256=current_hash, size=row['native_size'],
                      native_baseline_verified=False, proof=None, native_sources=[])
        matches = by_hash.get(current_hash)
        if matches:
            result.update(native_baseline_verified=True, proof='exact_native_file_bytes', native_sources=matches)
        elif row['native_size']:
            own_pixels = pixel_hash(path)
            for candidate, sha in by_name[path.stem.lower()]:
                if sha not in pixel_cache:
                    pixel_cache[sha] = pixel_hash(candidate)
                if pixel_cache[sha] == own_pixels:
                    result['native_sources'].append(relative(candidate))
            if result['native_sources']:
                result.update(native_baseline_verified=True, proof='exact_native_rgba_and_canvas')
            else:
                # Repainted/patched bytes are not deduplicated. An unchanged same-name native canvas
                # still proves that this is a native-sized replacement rather than an x2 export.
                for candidate, sha in by_name[path.stem.lower()]:
                    with Image.open(candidate) as image:
                        if list(image.size) == row['native_size']:
                            result['native_sources'].append(relative(candidate))
                if result['native_sources']:
                    result.update(native_baseline_verified=True, proof='same_name_native_canvas_modified_pixels')
        records.append(result)
    missing = []
    for row in scope['missing_references']:
        candidates = [relative(p) for p, _ in by_name[row['name'].lower()]]
        missing.append(dict(name=row['name'], native_candidates=candidates))
    summary = dict(files=len(records), native_baseline_verified=sum(r['native_baseline_verified'] for r in records),
                   remaining_by_root=dict(collections.Counter('/'.join(r['path'].split('/')[:3])
                       for r in records if not r['native_baseline_verified'])),
                   scope_sha256=hashlib.sha256((HERE / 'scope.json').read_bytes()).hexdigest(),
                   generation_started=False)
    (HERE / 'source_audit.json').write_text(json.dumps(dict(summary=summary,
        source_roots=[relative(p) for p in sources], files=records, missing_references=missing), indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    print('Missing reference candidates:', missing)


if __name__ == '__main__':
    main()
