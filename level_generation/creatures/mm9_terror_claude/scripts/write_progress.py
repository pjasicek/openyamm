#!/usr/bin/env python3
"""Merge the production record (JSON file) into creature_3d_progress.json, adding sha256 for every listed path
(keys 'references_hd' and 'selected': {role: path relative to the repo}). Usage: write_progress.py <record.json>"""
import hashlib, json, os, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
rec = json.loads(Path(sys.argv[1]).read_text())
for key in ('references_hd', 'selected'):
    for role, path in list(rec.get(key, {}).items()):
        p = REPO / path
        rec[key][role] = {'path': path, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None}
state = HERE / 'creature_3d_progress.json'
doc = json.loads(state.read_text())
doc.update(rec)
fd, tmp = tempfile.mkstemp(dir=HERE, suffix='.json')
with os.fdopen(fd, 'w') as f:
    json.dump(doc, f, indent=1)
os.replace(tmp, state)
print('progress', sorted(doc))
