#!/usr/bin/env python3
"""Replace (or add) bindings in assets_dev/worlds/xeen/models/actors.yml from a YAML file of entries (lane S).
The file's header comment is kept; every other entry is untouched. Usage: bind.py <entries.yml> [--note "<line>"]
A --note line is appended to the header comment (what changed)."""
import sys
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[3]
TARGET = REPO / 'assets_dev/worlds/xeen/models/actors.yml'
args = sys.argv[1:]
note = None
if '--note' in args:
    i = args.index('--note'); note = args[i + 1]; del args[i:i + 2]
new = yaml.safe_load(open(args[0]))['actors']
text = TARGET.read_text()
head, _ = text.split('\nactors:\n', 1)
doc = yaml.safe_load(text)
acts = doc['actors']
index = {e['descriptor']: i for i, e in enumerate(acts)}
for e in new:
    if e['descriptor'] in index:
        acts[index[e['descriptor']]] = e
    else:
        acts.append(e)
if note:
    head += '\n# ' + note
tmp = TARGET.with_name(TARGET.name + '.tmp')  # temp file + rename (hard-link scratch roots)
tmp.write_text(head + '\n' + yaml.dump({'actors': acts}, sort_keys=False, width=120))
tmp.chmod(0o644)
tmp.replace(TARGET)
print('BOUND', [e['descriptor'] for e in new], 'total', len(acts))
