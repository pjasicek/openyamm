#!/usr/bin/env python3
"""Append (or replace) this body's MM9 descriptor bindings in assets_dev/worlds/mm9/models/actors.yml.
Run under the shared lock: flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 ...
The file is re-read here and written by temp file + os.replace (assets_dev files are hard-linked into mirrors).
Usage: bind_actors.py <block.yml> <descriptor> [...]   (block = the comment + entries to insert, as YAML text)"""
import os, re, sys, tempfile
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
YML = REPO / 'assets_dev/worlds/mm9/models/actors.yml'
block = Path(sys.argv[1]).read_text()
descs = sys.argv[2:]
text = YML.read_text()
lines = text.splitlines(keepends=True)
# drop existing entries for these descriptors (an entry runs from its '- descriptor:' line to the next entry/comment)
out, skip = [], False
for ln in lines:
    m = re.match(r'- descriptor: (.*)$', ln.rstrip('\n'))
    if m:
        skip = m.group(1).strip() in descs
        if skip and out and out[-1].startswith('#'):
            out.pop()  # the entry's own note line
    elif skip and (ln.startswith('#') or ln.startswith('- ')):
        skip = False
    if not skip:
        out.append(ln)
text = ''.join(out)
blines = block.splitlines(keepends=True)
first = next(i for i, ln in enumerate(blines) if ln.startswith('- descriptor:'))
header = ''.join(blines[:max(0, first - 1)])   # the block's header comment (without the first entry's note)
if header and header in text:                  # from an earlier run
    text = text.replace(header, '')
if not text.endswith('\n'):
    text += '\n'
text += block if block.endswith('\n') else block + '\n'
fd, tmp = tempfile.mkstemp(dir=YML.parent, prefix='.actors.', suffix='.yml')
with os.fdopen(fd, 'w') as f:
    f.write(text)
os.chmod(tmp, 0o644)
os.replace(tmp, YML)
print('bound', descs)
