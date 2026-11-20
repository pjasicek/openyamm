"""Preserve hash-bound observations only after the listed images were visually inspected."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

REPO = Path(__file__).resolve().parents[5]


def record(paths, category, note):
    for value in paths:
        path = REPO / value
        review = next(parent for parent in path.parents if parent.name == 'review')
        target = review / 'manual_observations.json'
        data = json.loads(target.read_text()) if target.exists() else {'artifacts': [], 'observations': []}
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        archive = review / 'history' / ('viewed_' + digest[:16] + '.png')
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            shutil.copyfile(path, archive)
        data.setdefault('artifacts', []).append(dict(
            path=str(path.relative_to(REPO)), sha256=digest, category=category, reviewed=True,
            preserved_artifact=str(archive.relative_to(REPO)), observation=note, acceptance=False))
        target.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'recorded': len(paths), 'category': category, 'acceptance': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--category', required=True)
    parser.add_argument('--note', required=True)
    parser.add_argument('paths', nargs='+')
    args = parser.parse_args()
    record(args.paths, args.category, args.note)
