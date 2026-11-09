"""Pin named session evidence only after it has actually been visually inspected."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SESSION = HERE.parent


def pin(paths):
    path = HERE / 'reviewed_resume_paths.json'
    record = json.loads(path.read_text())
    evidence = record.setdefault('evidence_sha256', {})
    for name in paths:
        item = (SESSION / name).resolve()
        assert item.is_relative_to(SESSION), name
        evidence[name] = hashlib.sha256(item.read_bytes()).hexdigest()
    record['inspected_relative_paths'] = sorted(evidence)
    path.write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    pin(sys.argv[1:])
