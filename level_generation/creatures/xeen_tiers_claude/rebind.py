#!/usr/bin/env python3
"""Point existing Xeen bindings at a Xeen tier model: for each descriptor in the map, keep the binding (clips, scale,
attachments, events) and set model and skin. Usage: rebind.py <model path> <descriptor>=<skin> ... [--note "<line>"]"""
import sys
from pathlib import Path
import yaml
REPO = Path(__file__).resolve().parents[3]
TARGET = REPO / 'assets_dev/worlds/xeen/models/actors.yml'
args = sys.argv[1:]
note = None
if '--note' in args:
    i = args.index('--note'); note = args[i + 1]; del args[i:i + 2]
model, pairs = args[0], dict(a.split('=', 1) for a in args[1:])
text = TARGET.read_text()
head, _ = text.split('\nactors:\n', 1)
doc = yaml.safe_load(text)
done = []
for e in doc['actors']:
    if e['descriptor'] in pairs:
        e['model'] = model; e['skin'] = pairs[e['descriptor']]; done.append(e['descriptor'])
missing = set(pairs) - set(done)
if missing:
    raise SystemExit(f'not bound: {sorted(missing)}')
if note:
    head += '\n# ' + note
# temp file + rename: assets_dev files share inodes with hard-link scratch roots
tmp = TARGET.with_name(TARGET.name + '.tmp')
tmp.write_text(head + '\n' + yaml.dump({'actors': doc['actors']}, sort_keys=False, width=120))
tmp.chmod(0o644)
tmp.replace(TARGET)
print('REBOUND', done)
