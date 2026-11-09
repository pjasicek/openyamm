#!/usr/bin/env python3
"""Replace (or append) this project's marked block in assets_dev/worlds/mm9/models/actors.yml.

Usage (under the shared lock): flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock \\
    python3 <project>/scripts/bind_actors.py <marker> <block.yml>
The file is re-read inside the lock and written by temp file + os.replace (assets_dev is hard-linked into mirrors).
The result must parse as YAML and keep every other descriptor."""
import os, sys, tempfile
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[4]
PATH = REPO / 'assets_dev' / 'worlds' / 'mm9' / 'models' / 'actors.yml'
marker, block_path = sys.argv[1], Path(sys.argv[2])
block = block_path.read_text().rstrip('\n') + '\n'
start, end = f'# >>> {marker}\n', f'# <<< {marker}\n'
text = PATH.read_text()
before = yaml.safe_load(text)['actors']
if start in text and end in text:
    a = text.index(start); b = text.index(end) + len(end)
    text = text[:a] + start + block + end + text[b:]
else:
    text = text.rstrip('\n') + '\n' + start + block + end
after = yaml.safe_load(text)['actors']
mine = [e['descriptor'] for e in yaml.safe_load(block)]
others_before = [e['descriptor'] for e in before if e['descriptor'] not in mine]
others_after = [e['descriptor'] for e in after if e['descriptor'] not in mine]
assert others_before == others_after, 'other descriptors changed'
fd, tmp = tempfile.mkstemp(dir=PATH.parent, prefix='.actors.', suffix='.yml')
with os.fdopen(fd, 'w') as f:
    f.write(text)
os.chmod(tmp, 0o664)
os.replace(tmp, PATH)
print('bound', mine, 'total', len(after))
