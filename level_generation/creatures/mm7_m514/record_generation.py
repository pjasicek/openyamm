"""Preserve a built-in result with its exact prompt and references; never overwrite a version."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image

HERE = Path(__file__).resolve().parent


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=HERE)
    parser.add_argument('batch')
    parser.add_argument('version')
    parser.add_argument('generated', type=Path)
    parser.add_argument('--reference', action='append', required=True)
    parser.add_argument('--review', required=True)
    parser.add_argument('--accepted', action='store_true')
    args = parser.parse_args()
    root = args.project.resolve()
    destination = root / f'raw/{args.batch}_{args.version}.png'
    assert not destination.exists(), destination
    shutil.copy2(args.generated, destination)
    def asset(path):
        return dict(path=str(path.relative_to(root)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    prompt = root / f'prompts/submitted/{args.batch}_{args.version}.txt'
    assert prompt.exists(), 'Save exact submitted prompt before calling imagegen.'
    path = root / 'generation.json'
    data = json.loads(path.read_text())
    batch = data['batches'].setdefault(args.batch, {})
    batch.setdefault('attempts', []).append(dict(version=args.version, raw=asset(destination),
        original_output=str(args.generated), dimensions=Image.open(destination).size, prompt=asset(prompt),
        references=[asset(root / reference) for reference in args.reference], review=args.review,
        accepted=args.accepted, recorded_utc=datetime.now(timezone.utc).isoformat()))
    if args.accepted:
        batch['selected'] = str(destination.relative_to(root))
    path.write_text(json.dumps(data, indent=2)+'\n')


if __name__ == '__main__':
    run()
